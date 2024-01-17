![Web Scraping Image](web_scraping.jpeg)
# Confluence-Broken-Links
This script returns all unusable, malformed, or time-out links within a Confluence space. Used to maintain accurate documentation.

## Learnings:
During my tenure at the company, I encountered a documentation system that utilized Confluence as its backend. While working with this system, I observed a recurring issue where creating a reference link to an original page, followed by the deletion of the original page, would result in a broken link. It became evident that this issue required a resolution. Despite recognizing the need to report this bug to the platform, I discovered that numerous similar requests had already been submitted over the past few years without gaining much traction.

In response to this challenge, I took the initiative to develop a tool that could fulfill our objectives and provide customers with a seamless documentation collection. Since a significant portion of our documentation was client-facing, my goal was to create an automated solution capable of monitoring links in real-time and identifying any that were unusable, malformed, or timed out within 5 to 10 seconds. To achieve this, I needed to:

Understand the authentication process for the website.
Learn how to scrape the desired content.
Isolate the links within the content.
Test each link for validity, categorizing safe and failed links using a custom conditional hierarchy.
Compile a list of problematic links and automatically email it to a specific address, facilitating communication with the page owners for necessary updates.
One of the major challenges I encountered was the presence of different "spaces" within the system, each acting as its own domain for a collection of pages. Links on a page within one space could reference pages in other spaces, requiring me to devise a space-agnostic solution for retrieving references across multiple spaces and pages. This flexibility allowed users to specify a target space for scanning, enabling the detection of dependencies and links that needed attention.

This project marked a significant milestone in my career, as it underscored the impact of my work not only on my immediate team but also on cross-functional teams. Moreover, it provided valuable monitoring capabilities for other businesses utilizing Confluence as their backend. The accuracy and completeness of documentation are paramount, especially in sectors like healthcare, where access to specific healthcare provider data is crucial. I take pride in the successful completion of this task, as it allows me to deliver value to critical verticals in need of accurate and dependable documentation.

### Usage:
1. Install Python from [Python Downloads](https://www.python.org/downloads/).
2. Clone the Repository - ```git clone https://github.com/bvolesky/Confluence-Broken-Links.git```
3. Navigate to the Repository - ```cd <repository_folder>/Confluence-Broken-Links```
5. Run the App - ```python Confluence-Broken-Links.py```
This will allow the proper link tests to go through that some corporate firewalls automatically blocks.
