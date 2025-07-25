import os
import urllib.request
import pypdf
import shutil


def download(paper_urls: list) -> str:
    """
    Given a list of URLs or file paths to research papers,
    Downloads each paper
    Extracts the text content and returns it in a string in XML format.
    """
    papers_dir = os.path.join(os.environ.get("DATA_DIR", ".\data"), "data", "papers")
    if not os.path.exists(papers_dir):
        os.makedirs(papers_dir)

    print(paper_urls)
    paper_text = ""

    for i, paper_url in enumerate(paper_urls, start=1):
        text = ""
        try:
            if paper_url.startswith("http://") or paper_url.startswith("https://"):
                with urllib.request.urlopen(paper_url) as response:
                    if response.status == 200:

                        paper_path = os.path.join(papers_dir, f"paper_{i}.pdf")
                        with open(paper_path, 'wb') as file:
                            file.write(response.read())

                        reader = pypdf.PdfReader(paper_path)

                        for page_num, page in enumerate(reader.pages, start=1):
                            page_text = page.extract_text()
                            lines = page_text.split('\n')
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
                        
                            # Join the processed lines back into a page text
                            page_text = '\n\n'.join(processed_lines)
                        
                            # Add a header for each page
                            text += f"Page {page_num}:\n{page_text}\n\n"
                    else:
                        print(f"Failed to download {paper_url}: {response.status}")

            elif os.path.exists(paper_url):
                paper_path = os.path.join(papers_dir, os.path.basename(paper_url))
                shutil.copy(paper_url, paper_path)
                reader = pypdf.PdfReader(paper_path)
                
                for page_num, page in enumerate(reader.pages, start=1):
                    page_text = page.extract_text()
                    lines = page_text.split('\n')
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
                    
                    # Join the processed lines back into a page text
                    page_text = '\n\n'.join(processed_lines)
                    
                    # Add a header for each page
                    text += f"Page {page_num}:\n{page_text}\n\n"
            else:
                print(f"Invalid URL or file not found: {paper_url}")
            paper_text += f"\n<paper{i}>\n{text}\n</paper{i}>\n"
        except Exception as e:
            print(f"Failed to download or copy {paper_url}: {e}")
    return paper_text