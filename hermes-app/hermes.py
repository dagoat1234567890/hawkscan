import os
import json
import requests
from bs4 import BeautifulSoup
import anthropic
try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

# Try to import the official Hermes Agent from the NousResearch repository
try:
    from run_agent import AIAgent
    HERMES_AGENT_AVAILABLE = True
except ImportError:
    HERMES_AGENT_AVAILABLE = False

class HawkscanAgent:
    def __init__(self, api_key=None):
        self.anthropic_api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        
        if not self.anthropic_api_key:
            print("WARNING: ANTHROPIC_API_KEY not found. Hawkscan will not work.")
            
        if self.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        else:
            self.anthropic_client = None

    def _clean_url(self, url):
        """Strips query parameters and tracking garbage from URLs to save tokens."""
        if not url:
            return ""
        # Strip query parameters
        cleaned = url.split("?")[0]
        # Strip Amazon ref parameters
        if "amazon" in cleaned.lower():
            cleaned = cleaned.split("/ref=")[0]
        return cleaned

    def _request_with_retry(self, url, max_retries=3, method="GET", data=None, timeout_sec=10):
        import time
        import random
        
        try:
            from curl_cffi import requests as curl_requests
            use_curl = True
        except ImportError:
            use_curl = False
            
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        if method == "POST":
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        
        for attempt in range(max_retries):
            headers["User-Agent"] = random.choice(user_agents)
            try:
                if use_curl:
                    if method == "POST":
                        response = curl_requests.post(url, headers=headers, data=data, timeout=timeout_sec, impersonate="chrome120")
                    else:
                        response = curl_requests.get(url, headers=headers, timeout=timeout_sec, impersonate="chrome120")
                else:
                    if method == "POST":
                        response = requests.post(url, headers=headers, data=data, timeout=timeout_sec)
                    else:
                        response = requests.get(url, headers=headers, timeout=timeout_sec)
                        
                if response.status_code == 200:
                    return response
                elif response.status_code in [403, 429, 503]:
                    time.sleep(2 ** attempt + random.random())
                else:
                    return response
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Request to {url} failed: {e}")
                time.sleep(2 ** attempt + random.random())
        return None

    def _search_ddg_html(self, query):
        """Fetches and parses DuckDuckGo HTML search results directly to avoid client library errors."""
        import urllib.parse
        results = []
        
        # Try DDGS library first if available
        if DDGS:
            try:
                for r in DDGS().text(query, max_results=5):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "")
                    })
                if results:
                    return results
            except Exception as e:
                print(f"DDGS library error: {e}")

        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
        try:
            response = self._request_with_retry(url)
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                # Main selector: find all links that represent search snippets
                for a in soup.find_all("a", class_="result__snippet"):
                    href = a.get("href", "")
                    # Clean up DDG redirect URL if present
                    if "/l/?kh=" in href:
                        parsed = urllib.parse.urlparse(href)
                        qs = urllib.parse.parse_qs(parsed.query)
                        if "uddg" in qs:
                            href = qs["uddg"][0]
                    
                    href = self._clean_url(href)
                    title_elem = a.find_previous("a", class_="result__url")
                    title = title_elem.get_text(strip=True) if title_elem else "No Title"
                    snippet = a.get_text(strip=True)
                    
                    results.append({
                        "title": title,
                        "url": href,
                        "snippet": snippet
                    })
                
                # Backup selector: find by result__body if result__snippet isn't used
                if not results:
                    for div in soup.find_all("div", class_="result__body"):
                        link = div.find("a", class_="result__url")
                        snippet_elem = div.find("a", class_="result__snippet")
                        if link:
                            href = link.get("href", "")
                            if "/l/?kh=" in href:
                                parsed = urllib.parse.urlparse(href)
                                qs = urllib.parse.parse_qs(parsed.query)
                                if "uddg" in qs:
                                    href = qs["uddg"][0]
                            href = self._clean_url(href)
                            title = link.get_text(strip=True)
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                            results.append({
                                "title": title,
                                "url": href,
                                "snippet": snippet
                            })
        except Exception as e:
            print(f"DuckDuckGo HTML search error: {e}")
            
        if not results:
            # Fallback to DDG Lite
            try:
                lite_url = "https://lite.duckduckgo.com/lite/"
                lite_data = {"q": query}
                lite_res = self._request_with_retry(lite_url, method="POST", data=lite_data)
                if lite_res and lite_res.status_code == 200:
                    soup = BeautifulSoup(lite_res.text, "html.parser")
                    for tr in soup.find_all("tr"):
                        a = tr.find("a", class_="result-url")
                        snippet_td = tr.find_next_sibling("tr")
                        if a:
                            href = a.get("href", "")
                            if "//duckduckgo.com/l/?uddg=" in href:
                                parsed = urllib.parse.urlparse(href)
                                qs = urllib.parse.parse_qs(parsed.query)
                                if "uddg" in qs:
                                    href = qs["uddg"][0]
                            href = self._clean_url(href)
                            title = a.get_text(strip=True)
                            snippet = ""
                            if snippet_td:
                                snippet_elem = snippet_td.find("td", class_="result-snippet")
                                if snippet_elem:
                                    snippet = snippet_elem.get_text(strip=True)
                            results.append({
                                "title": title,
                                "url": href,
                                "snippet": snippet
                            })
            except Exception as e:
                print(f"DuckDuckGo Lite fallback error: {e}")
                
        if not results:
            print("Falling back to Bing search...")
            return self._search_bing_html(query)
            
        return results

    def _search_bing_html(self, query):
        """Fetches and parses Bing HTML search results directly."""
        import urllib.parse
        url = f"https://www.bing.com/search?q={urllib.parse.quote_plus(query)}"
        results = []
        try:
            # Custom Edge UA for Bing
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
                "Accept-Language": "en-US,en;q=0.9"
            }
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                for li in soup.find_all("li", class_="b_algo"):
                    title_elem = li.find("h2")
                    if not title_elem:
                        continue
                    a = title_elem.find("a")
                    if not a:
                        continue
                    title = a.get_text(strip=True)
                    href = self._clean_url(a.get("href", ""))
                    
                    snippet = ""
                    caption = li.find("div", class_="b_caption")
                    if caption:
                        p = caption.find("p")
                        if p:
                            snippet = p.get_text(strip=True)
                            
                    results.append({
                        "title": title,
                        "url": href,
                        "snippet": snippet
                    })
        except Exception as e:
            print(f"Bing search error: {e}")
            
        return results

    def _fetch_amazon_search_direct(self, product_name):
        """Fetches and parses Amazon search results directly to avoid search engine captcha blocks."""
        import urllib.parse
        url = f"https://www.amazon.ae/s?k={urllib.parse.quote_plus(product_name)}"
        results = []
        try:
            res = self._request_with_retry(url)
            if res and res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                products = soup.find_all("div", {"data-component-type": "s-search-result"})
                for p in products[:6]:
                    title_elem = p.find("h2")
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    link_elem = p.find("a", class_="a-link-normal s-no-outline")
                    href = "https://www.amazon.ae" + link_elem.get("href") if link_elem else ""
                    href = self._clean_url(href)
                    
                    card_text = p.get_text(separator=' ', strip=True)
                    
                    if title and href:
                        results.append({
                            "title": title,
                            "url": href,
                            "snippet": card_text[:1500]
                        })
        except Exception as e:
            print(f"Direct Amazon search error: {e}")
        return results

    def _fetch_noon_catalog_direct(self, url):
        """Fetches a specific Noon product page to bypass search."""
        try:
            from curl_cffi import requests as curl_requests
        except ImportError:
            import requests as curl_requests
            
        profiles = ["chrome120", "edge101", "safari15_3"]
        res = None
        for i in range(3):
            try:
                if hasattr(curl_requests, "impersonate"):
                    res = curl_requests.get(url, impersonate=profiles[i], timeout=10)
                else:
                    res = curl_requests.get(url, timeout=10)
                if res and res.status_code == 200:
                    break
            except Exception:
                import time
                time.sleep(1.5)
                
        if res and res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            text = soup.get_text(separator=' ', strip=True)
            return [{"title": soup.title.string if soup.title else "", "url": url, "snippet": text[:3000]}]
        return []

    def _fetch_noon_search_direct(self, product_name):
        """Fetches and parses Noon search results directly using their internal catalog API with curl_cffi to bypass Cloudflare."""
        import urllib.parse
        try:
            from curl_cffi import requests as curl_requests
        except ImportError:
            print("curl_cffi not installed, falling back to standard requests (may fail against Cloudflare).")
            import requests as curl_requests
            
        search_query = product_name
                
        url = f"https://www.noon.com/_svc/catalog/api/v3/u/search?q={urllib.parse.quote_plus(search_query)}&limit=100"
        results = []
        try:
            # Rotating profiles for retries
            profiles = ["chrome120", "edge101", "safari15_3"]
            res = None
            
            for i in range(3):
                try:
                    if hasattr(curl_requests, "impersonate"):
                        res = curl_requests.get(url, impersonate=profiles[i], timeout=10)
                    else:
                        res = curl_requests.get(url, timeout=10)
                    if res and res.status_code == 200:
                        break
                except Exception as e:
                    import time
                    time.sleep(1.5) # Short wait before next profile
                    
            if res and res.status_code == 200:
                data = res.json()
                for item in data.get("hits", []):
                    title = item.get("name", "")
                    price = item.get("sale_price") or item.get("price", 0)
                    brand = item.get("brand", "")
                    url_suffix = item.get("url", "")
                    
                    if title and url_suffix:
                        url_suffix = url_suffix.lstrip("/")
                        if "/p/" not in url_suffix:
                            sku = item.get("sku", "") or item.get("sku_config", "") or item.get("skuCode", "") or item.get("SKU", "")
                            if sku:
                                url_suffix = f"{url_suffix}/{sku}/p/"
                                
                        
                        if url_suffix.startswith("uae-en/") or url_suffix.startswith("egypt-en/") or url_suffix.startswith("saudi-en/"):
                            href = f"https://www.noon.com/{url_suffix}"
                        else:
                            href = f"https://www.noon.com/uae-en/{url_suffix}"
                        store_name = item.get("store_name") or item.get("store_code") or brand or "Unknown Seller"
                        results.append({
                            "title": title,
                            "url": href,
                            "snippet": f"Brand: {brand} | Store/Seller: {store_name} | Price: {price} AED | Title: {title}"
                        })
        except Exception as e:
            print(f"Direct Noon API search error: {e}")
        return results

    def _call_anthropic(self, messages, max_tokens=4000, temperature=0.1):
        """Sends a request to Anthropic API using Claude 3.5 Sonnet."""
        import time
        if not self.anthropic_client:
            raise RuntimeError("Anthropic client is not initialized. Please set ANTHROPIC_API_KEY in your .env file.")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print("Calling Anthropic...")
                response = self.anthropic_client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages
                )
                tokens_used = response.usage.input_tokens + response.usage.output_tokens
                return response.content[0].text.strip(), tokens_used
            except Exception as e:
                error_msg = str(e)
                print(f"Anthropic API call failed (attempt {attempt+1}/{max_retries}): {error_msg}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt + 3) # Wait 4s, 5s...
                else:
                    raise RuntimeError(f"Anthropic API call failed after {max_retries} attempts: {error_msg}")

    def _parse_json_response(self, raw_response):
        """Robustly extracts and parses JSON data from model responses."""
        text = raw_response.strip()
        
        # Add opening brace if it got truncated/cut off
        if text.startswith('parameters":'):
            text = "{" + text
            
        # Try direct parse
        try:
            return json.loads(text)
        except Exception:
            pass
            
        import re
        
        # Try finding ```json blocks and parse from last to first (as last is usually final)
        json_blocks = re.findall(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
        for block in reversed(json_blocks):
            try:
                return json.loads(block)
            except Exception:
                pass

        # Try stripping markdown blocks manually
        clean_text = text
        # Find first '{' and last '}'
        start_brace = clean_text.find('{')
        end_brace = clean_text.rfind('}')
        if start_brace != -1 and end_brace != -1:
            candidate = clean_text[start_brace:end_brace+1]
            try:
                data = json.loads(candidate)
                # Unwrap nested text/parameters JSON if present
                if isinstance(data, dict):
                    if "parameters" in data and isinstance(data["parameters"], dict) and "text" in data["parameters"]:
                        inner_text = data["parameters"]["text"]
                        try:
                            return json.loads(inner_text)
                        except Exception:
                            pass
                    if "text" in data and isinstance(data["text"], str):
                        try:
                            return json.loads(data["text"])
                        except Exception:
                            pass
                return data
            except Exception:
                pass
                
        # Find first '[' and last ']'
        start_bracket = clean_text.find('[')
        end_bracket = clean_text.rfind(']')
        if start_bracket != -1 and end_bracket != -1:
            candidate = clean_text[start_bracket:end_bracket+1]
            try:
                return json.loads(candidate)
            except Exception:
                pass
                
        raise ValueError(f"Could not parse response as JSON: {raw_response}")

    def fetch_web_data_fallback(self, url):
        """Fallback fetching if official Hermes Agent fails."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            # Reduced timeout to 2 seconds for maximum speed
            response = requests.get(url.strip(), headers=headers, timeout=2)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            return {"url": url, "text": text[:3000], "status": "success"}
        except Exception as e:
            return {"url": url, "text": f"Error fetching data: {str(e)}", "status": "error"}

    def analyze_custom_urls(self, product_name, company_name, my_url, competitor_urls):
        """Analyzes a specific set of URLs provided by the user."""
        listings = []
        
        if my_url:
            my_url = my_url.strip()
            if "noon.com" in my_url:
                cat = self._fetch_noon_catalog_direct(my_url)
                if cat: listings.extend(cat)
            else:
                text = self.fetch_web_data_fallback(my_url)
                if text: listings.append({"title": "Custom Catalog", "url": my_url, "snippet": text})
                
        for url in competitor_urls:
            url = url.strip()
            if not url: continue
            if "noon.com" in url:
                cat = self._fetch_noon_catalog_direct(url)
                if cat: listings.extend(cat)
            else:
                text = self.fetch_web_data_fallback(url)
                if text: listings.append({"title": "Competitor", "url": url, "snippet": text})
                
        if not listings:
            return self._error_response("Could not extract any data from the provided URLs.")
            
        prompt = f"""
        You are a highly analytical e-commerce market intelligence AI.
        
        The user wants to analyze prices for their specific product: '{product_name}' 
        sold by their company: '{company_name}'.
        
        Task:
        1. {"Extract our exact price ('my_price') from our official URL (" + my_url + ")." if my_url else f"Identify the listing sold by our company (which may appear as a variation of '{company_name}')."}
        2. Extract the competitor prices from the other URLs.
        3. Format the final output EXACTLY as JSON.
        
        JSON Schema:
        {{
            "my_price": 120.50, // Float or integer. Null if not found.
            "competitors": [
                {{
                    "url": "https://...",
                    "price": 1020.00,
                    "seller": "Competitor Name", // MUST NOT be '{company_name}' or any variation of it.
                    "title": "Exact product title on listing"
                }}
            ]
        }}
        
        Text extracted from the provided URLs:
        """
        
        for i, listing in enumerate(listings):
            prompt += f"\n[Listing {i+1}]\nURL: {listing['url']}\nText Snippet: {listing['snippet'][:1500]}\n"
            
        try:
            raw_response, tokens_used = self._call_anthropic([{"role": "user", "content": prompt}], max_tokens=1500, temperature=0.1)
            data = self._parse_json_response(raw_response)
            
            if not data:
                return self._error_response("Failed to parse prices from the AI response.")
                
            my_price = data.get("my_price")
            competitors = data.get("competitors", [])
            result = self._compute_market_position(product_name, my_price, competitors, "Custom Analysis")
            result['tokens_used'] = tokens_used
            return result
        except Exception as e:
            return self._error_response(f"Custom price analysis failed: {str(e)}")

    def analyze_prices(self, product_name, company_name, platform, catalog_url=None, target_competitors=None):
        if self.anthropic_api_key:
            return self._analyze_prices_official(product_name, company_name, platform, catalog_url, target_competitors)
        else:
            return self._error_response("ANTHROPIC_API_KEY is missing. Hawkscan is disabled.")
            
    def _analyze_prices_official(self, product_name, company_name, platform, catalog_url=None, target_competitors=None):
        """Uses a local search and scraping pipeline combined with a direct OpenRouter call for robust price extraction."""
        platform_lower = platform.lower()
        
        is_fallback = False
        original_platform = platform
        if "fallback for" in platform_lower:
            is_fallback = True
            # Extract original platform name
            # "amazon.ae (fallback for noon)" -> Noon
            original_platform = platform.split("Fallback for ")[-1].replace(")", "").strip()
            platform_domain = "amazon.ae"
            platform_source_label = "Amazon.ae (Fallback)"
        else:
            domain_map = {
                "amazon.ae": "amazon.ae",
                "noon": "noon.com",
                "careem": "careem.com"
            }
            platform_domain = domain_map.get(platform_lower, platform_lower.replace(" ", "") + ".com")
            platform_source_label = platform
            
        # 1. Try direct API scraping based on platform
        if "noon" in platform_lower and not is_fallback:
            listings = []
            if catalog_url and "noon.com" in catalog_url:
                print(f"Fetching exact catalog URL...")
                cat_listing = self._fetch_noon_catalog_direct(catalog_url)
                if cat_listing:
                    listings.extend(cat_listing)
            
            print(f"Fetching search results for competitors with ultra-fast API...")
            search_listings = self._fetch_noon_search_direct(product_name)
            
            # Search 2: Specific company search to guarantee our product is found even if buried
            company_query = f"{company_name.split()[0]} {product_name}"
            company_listings = self._fetch_noon_search_direct(company_query)
            
            # Prepend company listings so they are not cut off by the 50-item limit
            search_listings = company_listings + search_listings
            
            seen_urls = {l['url'] for l in listings}
            for s in search_listings:
                if s['url'] not in seen_urls:
                    listings.append(s)
                    seen_urls.add(s['url'])
                    
        elif "amazon" in platform_lower:
            listings = self._fetch_amazon_search_direct(product_name)
        else:
            listings = []
            
        # 2. Fall back to search engines if direct scrape returned nothing or if it's another platform
        if not listings:
            query1 = f"{product_name} site:{platform_domain}"
            listings.extend(self._search_ddg_html(query1))
            
            # Filter broad listings to ONLY include the target platform
            query2 = f"{product_name} {platform} price UAE"
            broad_listings = self._search_ddg_html(query2)
            
            # Avoid duplicates by URL and strictly filter by platform domain
            seen_urls = {item['url'] for item in listings}
            for b_item in broad_listings:
                if platform_domain in b_item['url'].lower() and b_item['url'] not in seen_urls:
                    listings.append(b_item)
                    seen_urls.add(b_item['url'])
                
            print(f"Found {len(listings)} listings from search. Fetching product page details...")
            
            # Fetch detailed content for the top 3 results to extract accurate price data
            for item in listings[:3]:
                url = item["url"]
                try:
                    res = self._request_with_retry(url, max_retries=1, timeout_sec=5)
                    if res and res.status_code == 200:
                        soup = BeautifulSoup(res.text, 'html.parser')
                        text = soup.get_text(separator=' ', strip=True)
                        item["page_content"] = text[:1500]
                    else:
                        item["page_content"] = f"Failed directly: HTTP {res.status_code if res else 'Unknown'}"
                except Exception as e:
                    item["page_content"] = f"Failed directly: {str(e)}"
        else:
            print(f"Direct {platform} search returned {len(listings)} listings. Bypassing detail fetches.")
            
        # 3. Fallback to Amazon.ae direct search if no listings found for non-Amazon platform
        if not listings and not is_fallback and "amazon" not in platform_lower:
            print(f"No listings found for {original_platform}. Falling back to Amazon.ae search...")
            return self._analyze_prices_official(product_name, company_name, f"Amazon.ae (Fallback for {original_platform})", catalog_url)
                 
        catalog_text = ""
        if catalog_url and not is_fallback:
            try:
                try:
                    from curl_cffi import requests as curl_requests
                    res = curl_requests.get(catalog_url, impersonate="chrome120", timeout=10)
                except ImportError:
                    res = self._request_with_retry(catalog_url, max_retries=1, timeout_sec=5)
                    
                if res and res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    catalog_text = soup.get_text(separator=' ', strip=True)[:1500]
                else:
                    print(f"Catalog URL fetch failed with status {res.status_code if res else 'Unknown'}")
            except Exception as e:
                print(f"Failed to fetch catalog URL: {e}")

        prompt = f"""
        You are Hawkscan, an expert market analyst agent.
        Your task is to analyze price information from search snippets and webpage contents for the product '{product_name}' on '{platform_source_label}'.
        
        {f"CRITICAL: The user provided their official product URL: {catalog_url}." if catalog_url else ""}
        {f"We fetched its text: '{catalog_text}'. You must extract 'my_price' from this text if possible. IF NOT FOUND in the text, you MUST check the 'Market listings found' below to see if any URL matches {catalog_url} and use its price as 'my_price'." if catalog_url else ""}
        """
        
        if is_fallback:
            prompt += f"""
            NOTE: The user originally requested tracking on '{original_platform}', but because that site is blocking scraping requests or has no results, we fell back to search on 'Amazon.ae' as a market reference.
            """
        
        prompt += f"""
        Sometimes the user might ask different questions about other ecomerce questions. Your task is to go to the specific page mentioed in the question
        and fetch the specific information asked by the user.

        We found the following listings on the web:
        """
        for i, item in enumerate(listings[:50], 1):
            prompt += f"""
        Listing #{i}:
        - Title: {item['title']}
        - URL: {item['url']}
        - Search Snippet: {item['snippet']}
        - Page Text: {item.get('page_content', 'N/A')}
        """
        
        prompt += f"""
        Task:
        1. {f"Extract our exact price ('my_price') from the official product URL provided above ({catalog_url}). IF YOU CANNOT FIND IT, fall back to identifying the listing sold by our company (which may appear as a variation of '{company_name}', or even just '{company_name.split()[0]}'), and extract its price." if catalog_url else f"Identify the listing sold by our company (which may appear as a variation of '{company_name}', or even just '{company_name.split()[0]}'). If there are multiple, pick the one that closest matches the requested product."} 
        2. CRITICAL FOR MY_PRICE: Verify that the 'Title' of the product matches the requested product specs: '{product_name}'. However, be extremely lenient with purely cosmetic variations: if our company sells a blue version or special packaging, and the requested product is generic, ACCEPT IT as 'my_price'. If our exact product is completely missing, set "my_price" to null.
        3. Identify real competitor listings ONLY from '{platform_domain}'. Ignore listings from other websites. CRITICAL: Do NOT extract any listings as competitors if the seller contains the word '{company_name.split()[0]}'! They are our own products!
        4. CRITICAL SPECIFICATION CHECK: Verify that the competitor product core specifications match '{product_name}'. Ensure all extracted prices are in AED.
           - KEYWORD STRICTNESS: The competitor title MUST logically represent the same core product. If '{product_name}' is a device, do NOT extract cases, screen protectors, or accessories. If it is a gold/silver bar, do NOT extract necklaces, jewelry, or coins.
           - MATERIAL MATCHING: If '{product_name}' specifies "Gold", REJECT any product containing "Silver". If '{product_name}' specifies "Silver", REJECT any product containing "Gold".
           - CONDITION STRICTNESS: Do NOT extract prices for 'Renewed', 'Refurbished', or 'Used' products UNLESS '{product_name}' explicitly contains those words! Additionally, if a single listing contains multiple prices (e.g. 'AED 355' and 'Used: AED 345' or 'More Buying Choices: AED 345'), you MUST extract the primary 'New' price (355) and completely IGNORE the secondary/used prices.
           - VARIANT LENIENCY: Be lenient with purely cosmetic variations (like color), BUT the core model, hardware, weight/capacity (e.g. 100g, 1 Ounce, 128GB), and brand MUST strictly match!
"""
        if target_competitors:
            prompt += f"""        5. CRITICAL COMPETITOR FILTER: ONLY extract competitor listings if the Store/Seller name matches or contains one of the following: {target_competitors}. Completely ignore any sellers not in this list. Do NOT extract them under any circumstances.
"""
        
        prompt += """
        6. EXTRACTING PRICES: Output the extracted data exactly matching the JSON Schema below.
           - **CRITICAL: PRESERVE CENTS/DECIMALS!** If a price appears as 'AED 397 . 02' or '397.02', you MUST extract `397.02`. Do NOT round to `397.0`. Always keep the exact decimal value.
        """
        prompt += f"""
        Format the output EXACTLY as JSON. If no valid competitor is found (e.g., you are the sole seller), return an empty list for competitors. DO NOT include markdown formatting. DO NOT include explanation text or reasoning. ONLY output valid JSON.        
        JSON Schema:
        {{
            "my_price": 1050.00,
            "my_url": "https://{platform_domain}/our-product-url",
            "competitors": [
                {{"url": "https://{platform_domain}/example-product", "price": 1020.50, "seller": "Competitor A", "title": "Apple iPhone 15 Pro Max 256GB"}},
                {{"url": "https://{platform_domain}/example-product-2", "price": 1045.00, "seller": "Competitor B", "title": "iPhone 15 Pro Max (256GB) - Blue Titanium"}}
            ]
        }}
        """
        
        try:
            messages = [{"role": "user", "content": prompt}]
            raw_json, tokens_used = self._call_anthropic(messages, max_tokens=4000)
            data = self._parse_json_response(raw_json)
            my_price = data.get("my_price")
            my_url = data.get("my_url")
            competitors = data.get("competitors", [])
            
            # If it's a fallback run, add warning to conclusion
            result = self._compute_market_position(product_name, my_price, competitors, f"Hawkscan Scraper ({platform_source_label})", my_url)
            result['tokens_used'] = tokens_used
            if is_fallback:
                result["conclusion"] = f"⚠️ Could not find exact product on {original_platform}. Showing reference prices from Amazon.ae instead: " + result["conclusion"]
                
            # CATALOG URL VALIDATION
            if catalog_url and not is_fallback and isinstance(my_price, (int, float)):
                avg_scraped = result.get("stats", {}).get("avg")
                if avg_scraped:
                    variance = abs(my_price - avg_scraped) / avg_scraped
                    if variance > 0.40:
                        return self._error_response(f"Inaccurate Catalog: The price on your provided link (AED {my_price:.2f}) is wildly unrealistic compared to the market average (AED {avg_scraped:.2f}). Please verify your catalog link.")
                        
            return result
        except Exception as e:
            return self._error_response(f"Price analysis failed: {str(e)}")

    def _compute_market_position(self, product_name, my_price, competitors, platform_source, my_url=None):
        valid_prices = [c["price"] for c in competitors if isinstance(c.get("price"), (int, float))]
        
        if not valid_prices:
            if my_price is not None and my_price != "Not Found":
                return {
                    "platform": platform_source,
                    "my_price": my_price,
                    "competitors": [],
                    "conclusion": "You appear to be the only seller for this specific product on this platform! No competitor prices found.",
                    "position": "Sole Seller",
                    "stats": {"min": None, "max": None, "avg": None}
                }
            else:
                return self._error_response("No listings for this product could be found on the platform. Please verify the product name or provide an exact catalog link.")
            
        min_price = min(valid_prices)
        max_price = max(valid_prices)
        avg_price = sum(valid_prices) / len(valid_prices)
        
        if my_price is None or not isinstance(my_price, (int, float)):
            return {
                "platform": platform_source,
                "my_price": "Not Found",
                "competitors": competitors,
                "conclusion": f"Could not find a listing for your company for '{product_name}' on this platform. Competitors average at AED {avg_price:.2f}.",
                "position": "Unknown",
                "stats": {
                    "min": min_price,
                    "max": max_price,
                    "avg": round(avg_price, 2)
                }
            }
            
        if my_price < min_price:
            position = "Cheapest"
            conclusion = f"You are the cheapest! The lowest competitor is AED {min_price:.2f}."
        elif my_price > max_price:
            position = "Most Expensive"
            conclusion = f"You are the most expensive. The highest competitor is AED {max_price:.2f}."
        elif my_price == min_price:
            position = "Tied for Cheapest"
            conclusion = f"You are tied for the lowest price at AED {min_price:.2f}."
        elif my_price == max_price:
            position = "Tied for Most Expensive"
            conclusion = f"You are tied for the highest price at AED {max_price:.2f}."
        else:
            position = "Average"
            conclusion = f"Your price is in the middle of the pack. Average is AED {avg_price:.2f}."        
        min_url = next((c.get("url") for c in competitors if c.get("price") == min_price), None)
        max_url = next((c.get("url") for c in competitors if c.get("price") == max_price), None)
        
        min_seller = next((c.get("seller") for c in competitors if c.get("price") == min_price and c.get("seller")), "Unknown Seller")
        max_seller = next((c.get("seller") for c in competitors if c.get("price") == max_price and c.get("seller")), "Unknown Seller")
        min_title = next((c.get("title") for c in competitors if c.get("price") == min_price and c.get("title")), "Unknown Title")
        max_title = next((c.get("title") for c in competitors if c.get("price") == max_price and c.get("title")), "Unknown Title")
        
        return {
            "platform": platform_source,
            "my_price": my_price,
            "my_url": my_url,
            "competitors": competitors,
            "conclusion": conclusion,
            "position": position,
            "stats": {
                "min": min_price,
                "min_url": min_url,
                "min_seller": min_seller,
                "min_title": min_title,
                "max": max_price,
                "max_url": max_url,
                "max_seller": max_seller,
                "max_title": max_title,
                "avg": round(avg_price, 2)
            }
        }

    def _error_response(self, message):
        return {
            "error": True,
            "message": message,
            "platform": "Error",
            "my_price": "Error",
            "competitors": [],
            "conclusion": message,
            "position": "Error",
            "stats": {"min": None, "max": None, "avg": None, "min_url": None, "max_url": None, "min_seller": None, "max_seller": None, "min_title": None, "max_title": None}
        }

    def chat(self, message, history=None, user_id=None):
        system_prompt = """
        You are Hawkscan, an AI agent for a competitive price-analysis and ecommerce web application. 
        You are flexible and can help the user with anything related to ecommerce.
        You have execution tools that can automatically add products, delete products, and update target competitors directly in the user's database.
        When asked to modify products or competitors, USE YOUR TOOLS to execute the action immediately, then confirm it was done.
        If the user asks for real-time prices, product searches, or competitive data, ALWAYS use the `search_market` tool to fetch live data from the web before answering.
        CRITICAL: When providing product listings, search results, or prices to the user, you MUST ALWAYS include clickable markdown links to the actual products (e.g., [Product Name](url)). Never return an unclickable URL.
        """
        
        tools = [
            {
                "name": "search_market",
                "description": "Searches the web for real-time e-commerce listings and prices for a specific product.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "product_name": {
                            "type": "string",
                            "description": "The name of the product to search for, e.g. 'Apple iPhone 15 Pro 256GB' or 'L\\'Oreal Shampoo 400ml'."
                        },
                        "platform": {
                            "type": "string",
                            "description": "The e-commerce platform to search on, e.g. 'Amazon.ae' or 'Noon'. If none is specified, use 'Amazon.ae'."
                        }
                    },
                    "required": ["product_name"]
                }
            },
            {
                "name": "add_product",
                "description": "Adds a new product tracker to the user's dashboard.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "product_name": {"type": "string", "description": "The name of the product."},
                        "company_name": {"type": "string", "description": "The company name selling the product."},
                        "platform": {"type": "string", "description": "The e-commerce platform, e.g. 'Amazon.ae' or 'Noon'."}
                    },
                    "required": ["product_name", "company_name", "platform"]
                }
            },
            {
                "name": "delete_product",
                "description": "Deletes an existing product tracker from the user's dashboard.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "product_name": {"type": "string", "description": "The exact name of the product to delete."}
                    },
                    "required": ["product_name"]
                }
            },
            {
                "name": "update_competitors",
                "description": "Updates the user's target competitors filter string.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "competitors_string": {"type": "string", "description": "Comma-separated list of target competitors, or empty string to clear."}
                    },
                    "required": ["competitors_string"]
                }
            },
            {
                "name": "get_dashboard_data",
                "description": "Fetches the user's current tracked products, their prices, and market averages from the database. Use this when the user asks about their own tracked products or dashboard.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]

        if not self.anthropic_client:
            return "Anthropic API key is not configured. Please set ANTHROPIC_API_KEY in your .env file."

        try:
            messages = []
            if history:
                for msg in history:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": message})
            
            # Max 3 tool execution turns to prevent infinite loops
            for _ in range(3):
                response = self.anthropic_client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    system=system_prompt,
                    max_tokens=2000,
                    temperature=0.1,
                    messages=messages,
                    tools=tools
                )
                
                if response.stop_reason == "tool_use":
                    # Append assistant response with tool use blocks
                    messages.append({"role": "assistant", "content": response.content})
                    
                    tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
                    tool_results = []
                    
                    for block in tool_use_blocks:
                        if block.name == "search_market":
                            product_name = block.input.get("product_name")
                            platform = block.input.get("platform", "Amazon.ae")
                            
                            print(f"Tool called: search_market for {product_name} on {platform}")
                            
                            # Call our existing scrapers
                            platform_lower = platform.lower()
                            if "amazon" in platform_lower:
                                listings = self._fetch_amazon_search_direct(product_name)
                            elif "noon" in platform_lower:
                                listings = self._fetch_noon_search_direct(product_name)
                            else:
                                domain_map = {"careem": "careem.com"}
                                platform_domain = domain_map.get(platform_lower, platform_lower + ".com")
                                query = f"{product_name} site:{platform_domain}"
                                listings = self._search_ddg_html(query)
                                
                            tool_result_text = json.dumps(listings[:5]) if listings else "No listings found for this query."
                            
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": tool_result_text
                            })
                        elif block.name == "add_product" and user_id:
                            product_name = block.input.get("product_name")
                            company_name = block.input.get("company_name")
                            platform = block.input.get("platform")
                            try:
                                import sqlite3
                                conn = sqlite3.connect('users.db')
                                c = conn.cursor()
                                c.execute("INSERT INTO trackers (user_id, product_name, company_name, platform) VALUES (?, ?, ?, ?)", (user_id, product_name, company_name, platform))
                                conn.commit()
                                conn.close()
                                tool_result_text = "Successfully added product to database."
                            except Exception as e:
                                tool_result_text = f"Error adding product: {e}"
                            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": tool_result_text})
                        elif block.name == "delete_product" and user_id:
                            product_name = block.input.get("product_name")
                            try:
                                import sqlite3
                                conn = sqlite3.connect('users.db')
                                c = conn.cursor()
                                c.execute("DELETE FROM trackers WHERE user_id = ? AND product_name = ?", (user_id, product_name))
                                conn.commit()
                                conn.close()
                                tool_result_text = "Successfully deleted product from database."
                            except Exception as e:
                                tool_result_text = f"Error deleting product: {e}"
                            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": tool_result_text})
                        elif block.name == "update_competitors" and user_id:
                            competitors_string = block.input.get("competitors_string")
                            try:
                                import sqlite3
                                conn = sqlite3.connect('users.db')
                                c = conn.cursor()
                                c.execute("UPDATE users SET target_competitors = ? WHERE id = ?", (competitors_string, user_id))
                                conn.commit()
                                conn.close()
                                tool_result_text = "Successfully updated target competitors."
                            except Exception as e:
                                tool_result_text = f"Error updating competitors: {e}"
                            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": tool_result_text})
                        elif block.name == "get_dashboard_data" and user_id:
                            try:
                                import sqlite3
                                conn = sqlite3.connect('users.db')
                                c = conn.cursor()
                                c.execute("SELECT product_name, company_name, platform, last_price, last_market_avg FROM trackers WHERE user_id = ?", (user_id,))
                                rows = c.fetchall()
                                conn.close()
                                if rows:
                                    dash_data = [{"product": r[0], "company": r[1], "platform": r[2], "your_price": r[3], "market_avg": r[4]} for r in rows]
                                    tool_result_text = json.dumps(dash_data)
                                else:
                                    tool_result_text = "You are not tracking any products yet."
                            except Exception as e:
                                tool_result_text = f"Error fetching dashboard data: {e}"
                            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": tool_result_text})
                            
                    if tool_results:
                        messages.append({
                            "role": "user",
                            "content": tool_results
                        })
                    else:
                        break
                else:
                    # Final response (text) received
                    text_blocks = [block.text for block in response.content if block.type == "text"]
                    return "".join(text_blocks).strip()
            
            # Fallback if loop finishes without stopping
            text_blocks = [block.text for block in response.content if block.type == "text"]
            return "".join(text_blocks).strip()

        except Exception as e:
            return f"Error communicating with Anthropic: {e}"
