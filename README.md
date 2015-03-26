# hacker-news-scrap (WIP)
A simple python command line tool to scrape [https://news.ycombinator.com](), the arguments it takes in are (startPost#,endPost#,outputFile) and outputs a CSV in the following format: 
[Post | comment], Post Permalink, points, First 150 characters of post title, Poster, URL to poster history
[Post | comment], Comment PermaLink,(leave blank), First 150 characters of comment, Poster, URL to poster history
Basically it scrapes the posts and its comments and outputs it to a CSV.