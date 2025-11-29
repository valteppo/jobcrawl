import asyncio
import aiohttp

async def fetch_url(session: aiohttp.ClientSession, url: str)-> str:
    """
    Asynchronously fetches the content of a URL.

    Args:
        session: aiohttp ClientSession object for connection
pooling.
        url: The URL to fetch.

    Returns:
        The content of the URL as a string, or None if an
error occurs.
    """
    try:
        async with session.get(url) as response:
            response.raise_for_status()  
            return await response.text()
    except aiohttp.ClientError as e:  
        print(f"Error fetching {url}: {e}")
        return None 

async def query_urls_async(urls: list[str]) -> list[str |
None]:
    """
    Asynchronously queries a list of URLs and returns a list
of their content.

    Args:
        urls: A list of URLs to query.

    Returns:
        A list of strings, where each string is the content
of the corresponding URL.
        Returns None for URLs that failed to fetch.
    """
    async with aiohttp.ClientSession() as session:  
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)  
        return results



async def main():
    """Example usage"""
    urls = [
        "https://www.example.com",
        "https://www.python.org",
        "https://httpstat.us/500", 
        "https://www.google.com"
    ]

    content_list = await query_urls_async(urls)

    for i, content in enumerate(content_list):
        if content:
            print(f"Content from {urls[i]}:\n{content[:100]}...\n") # print first 100 chars
        else:
            print(f"Failed to retrieve content from {urls[i]}\n")


if __name__ == "__main__":
    asyncio.run(main())