import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def crawl(urls: list) -> str:
    """
    Given a list of website URLs
    Extracts all links from each website
    Retrieves the text content from each link
    Returns the text content in a string in XML format
    """
    extracted_text = ""
    websites_dir = os.path.join("data", "websites")

    if not os.path.exists(websites_dir):
        try:
            os.makedirs(websites_dir)
        except PermissionError:
            print(f"Permission denied: unable to create directory {websites_dir}. Skipping...")
            return extracted_text
        except OSError as e:
            print(f"OS error: {e}. Skipping...")
            return extracted_text
        
    for i, url in enumerate(urls, start=1):
        extracted_text += f"\n<Website{i}>\n"
        website_dir = os.path.join(websites_dir, f"website_{i}")

        if not os.path.exists(website_dir):
            try:
                os.makedirs(website_dir)
            except PermissionError:
                print(f"Permission denied: unable to create directory {website_dir}. Skipping...")
                continue
            except OSError as e:
                print(f"OS error: {e}. Skipping...")
                continue

        try:
            # Send a GET request to the URL
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Save the HTML content to a file
            with open(os.path.join(website_dir, 'index.html'), 'w', encoding='utf-8') as file:
                file.write(response.text)

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Download resources (images, CSS, JavaScript files, etc.)
            for tag in soup.find_all(['img', 'link', 'script']):
                if tag.has_attr('src'):
                    resource_url = urljoin(url, tag['src'])
                elif tag.has_attr('href'):
                    resource_url = urljoin(url, tag['href'])
                else:
                    continue
                try:
                    resource_response = requests.get(resource_url)
                    resource_response.raise_for_status()

                    # Save the resource to a file
                    resource_path = urlparse(resource_url).path
                    resource_path = resource_path.lstrip('/')
                    if resource_path.endswith('/'):
                        # resource_path is a directory, skip it
                        continue

                    resource_dir = os.path.dirname(os.path.join(website_dir, resource_path))
                    if not os.path.exists(resource_dir):
                        try:
                            os.makedirs(resource_dir, exist_ok=True)
                        except PermissionError:
                            print(f"Permission denied: unable to create directory {resource_dir}. Skipping...")
                            continue
                        except OSError as e:
                            print(f"OS error: {e}. Skipping...")
                            continue

                    if resource_url.endswith(('jpg', 'jpeg', 'png', 'gif', 'bmp', 'ico')):
                        with open(os.path.join(website_dir, resource_path), 'wb') as file:
                            file.write(resource_response.content)
                    else:
                        with open(os.path.join(website_dir, resource_path), 'w', encoding='utf-8') as file:
                            file.write(resource_response.text)

                    # Update the tag to reference the local resource
                    if tag.has_attr('src'):
                        tag['src'] = resource_path
                    elif tag.has_attr('href'):
                        tag['href'] = resource_path
                except requests.RequestException as e:
                    print(f"Failed to download {resource_url}: {e}")

            # Extract all links from the page
            links = set()
            link_mapping = {}

            for link in soup.find_all('a', href=True):
                href = link['href']
                # Convert relative URLs to absolute URLs
                absolute_url = urljoin(url, href)
                parsed_url = urlparse(absolute_url)

                # Filter out non-http(s) links and links with fragments or query params
                if parsed_url.scheme in ['http', 'https'] and not parsed_url.fragment and not parsed_url.query and urlparse(url).netloc == parsed_url.netloc:
                    links.add(absolute_url)
                    # Map the original link to a local link
                    link_path = urlparse(absolute_url).path
                    link_path = link_path.lstrip('/')

                    if link_path == '':
                        link_path = 'index.html'
                    elif link_path.endswith('/'):
                        link_path += 'index.html'
                    link_mapping[absolute_url] = link_path

            # Update the links in the HTML to reference local links
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(url, href)
                if absolute_url in link_mapping:
                    link['href'] = link_mapping[absolute_url]

            # Save the updated HTML content to a file
            with open(os.path.join(website_dir, 'index.html'), 'w', encoding='utf-8') as file:
                file.write(str(soup))

            # Extract text from each link
            for j, link in enumerate(links, start=1):
                try:
                    link_response = requests.get(link)
                    link_response.raise_for_status()
                    link_soup = BeautifulSoup(link_response.text, 'html.parser')

                    # Save the link HTML content to a file
                    link_path = link_mapping[link]
                    link_dir = os.path.dirname(os.path.join(website_dir, link_path))
                    if not os.path.exists(link_dir):
                        try:
                            os.makedirs(link_dir, exist_ok=True)
                        except PermissionError:
                            print(f"Permission denied: unable to create directory {link_dir}. Skipping...")
                            continue
                        except OSError as e:
                            print(f"OS error: {e}. Skipping...")
                            continue
                    with open(os.path.join(website_dir, link_path), 'w', encoding='utf-8') as file:
                        file.write(str(link_soup))

                    link_text = link_soup.get_text()
                    lines = link_text.split('\n')
                    processed_lines = []
                    paragraph = ""

                    for line in lines:
                        stripped_line = line.strip()
                        # Remove excessive whitespace
                        stripped_line = ' '.join(stripped_line.split())
                        # Accumulate lines into a paragraph until a certain length is reached
                        if len(paragraph) + len(stripped_line) < 150:
                            paragraph += stripped_line + " "
                        else:
                            processed_lines.append(paragraph.strip())
                            paragraph = stripped_line + " "

                    # Add the last paragraph
                    if paragraph:
                        processed_lines.append(paragraph.strip())
                        
                    # Join the processed lines back into a link text
                    link_text = '\n\n'.join(processed_lines)
                    extracted_text += f"\n<link{j}>\n{link_text}</link{j}>\n"
                except requests.RequestException as e:
                    print(f"Failed to access {link}: {e}")
        except requests.RequestException as e:
            # Handle any exceptions that occur during the request
            print(f"An error occurred while accessing {url}: {e}")
        extracted_text += f"</Website{i}>\n"
    return extracted_text