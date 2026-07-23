# Hermes: Product Analyzer & Sales Accelerator

## Overview
Hermes is an intelligent price analysis and sales acceleration platform designed specifically for the e-commerce ecosystem, with a primary focus on Amazon and Noon. In highly competitive markets, a microscopic price difference—like pricing a gold bar at 499 AED versus 500 AED—can capture the entire market share. 

This platform leverages a central Large Language Model (LLM) to orchestrate real-time competitor scraping, analyze pricing gaps, and deliver actionable, formatted insights through a seamless chat-based UI.

## Business Models

### 🏢 B2B (For Amazon & Noon Sellers)
* **Competitive Product Analysis:** Sellers can input their products into the platform to instantly analyze how their pricing stacks up against direct competitors.
* **Buy-Box Optimization:** Identifies micro-pricing opportunities to help sellers adjust their prices strategically and accelerate their sales volume.

### 🛍️ B2C (For Everyday Consumers)
* **Conversational Deal Finder:** A chat interface where users can simply ask, "What's the cheapest price for [Product]?"
* **Instant Price Comparison:** The system scans multiple platforms (Amazon, Noon) to return the absolute lowest available price directly in the chat.

## How It Works (Workflow & Architecture)
The system is uniquely built around a central LLM that acts as the "brain" of the operation, orchestrating the entire data pipeline:

1. **Task Delegation:** The central LLM receives the user query from the UI and triggers the appropriate scraping APIs and fetching tools.
2. **Data Extraction:** The scraping tools execute targeted fetches on Amazon and Noon to retrieve live pricing and product data.
3. **Data Structuring:** The raw scraped data is passed back to the LLM. 
4. **Formatting & UI Delivery:** The LLM cleans, processes, and structures the unstructured data into a standardized format (such as markdown tables or conversational chat responses) and delivers it to the frontend UI.

## Tech Stack
* **Orchestration:** Central Large Language Model (LLM)
* **Web Scraping & Fetching:** `beautifulsoup4`, `cffi`, and many other tools
* **Interface:** Chat-based UI with dynamic table rendering
* **Language:** Python 
