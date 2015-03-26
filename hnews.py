#!/usr/bin/python

#==========================================================================
# IMPORTS
#==========================================================================
import sys
from optparse import OptionParser
import urllib2
from lxml import html
import csv

#==========================================================================
# CONSTANTS
#==========================================================================
NUMBERS = ["%c"%x for x in range(0x30,0x3A)]
NUMBER_POSTS_PER_PAGE = 30
URL_BASE="https://news.ycombinator.com/"

#==========================================================================
# FUNCTIONS
#==========================================================================

# Parse command line flags
def parseCommandLineFlags():
    parser = OptionParser(usage='%prog [OPTIONS] "string"',
                          version='%prog 0.1')
    
    parser.add_option('-v', '--verbose', type='int', default=0,
                      help='Increase verbosity level')

    parser.add_option('-r', '--readfile', type='str',
                      help='Read from a file')
    
    parser.add_option('-w', '--writefile', type='str',
                      help='Write to a file')
    
    parser.add_option('-d', '--dos', action="store_true",
                      help='Use DOS end of line characters (\\r\\n).  By default, \
                           this program outputs UNIX end of line characters (\\n).')
    
    if (len(sys.argv) == 1):
        parser.print_help()
        sys.exit()
    
    (options,args)=parser.parse_args()
    return options, args


# Print debug messages at the user specified verbosity level
def debug(level, message):
    if level <= options.verbose:
        sys.stderr.write(message + '\n')
    return


# Read file and return data as a LIST of stripped strings
def readFile(filename):
    lines = []
    with open(filename) as f:
        for line in f:
            if line.strip() != '':
                lines.append(line.strip())
        ##### If you want to preserve your lines in their original state, remove
        ##### the for loop above and use the following line instead.  You'll
        ##### also need to modify the writeFile fuction not to print newlines.
        #lines = f.readlines()
    return lines


# Write LIST to a file with either DOS or *NIX line endings
def writeFile(filename, lines):
    with open(filename, 'w') as f:
        for line in lines:
            if options.dos:
                f.writelines( ''.join( [line, '\r\n'] ) )
            else:
                f.writelines( ''.join( [line, '\n'] ) )
    return

def getPageFromPostId(postid):
    pid = int(postid) - 1  # starts from 0
    page = (1 + (pid / NUMBER_POSTS_PER_PAGE))
    return page

def createPageUrls(start,end):
    pages = []
    for i in range(start,end+1):
        pages.append(URL_BASE+'news?p='+str(i))
    return pages

def loadPageUrl(url):
    response = urllib2.urlopen(url)
    html = response.read()
    return html

def filter1of3(list):
    filtered = []
    for i in range(len(list)):
        if i % 3 == 0:
            filtered.append(list[i])
    return filtered

def filter2of3(list):
    filtered = []
    for i in range(len(list)):
        if i % 3 == 1:
            filtered.append(list[i])
    return filtered
  
def appendUrl(posterUrl):
    urls = []
    for i in posterUrl:
        urls.append(URL_BASE+i)
    return urls


def scrapeAllPosts(page):
    tree = html.fromstring(page)

    # not yet
    typePost = ["Post"] * NUMBER_POSTS_PER_PAGE
    intro = [""] * NUMBER_POSTS_PER_PAGE 

    postIds = tree.xpath('//span[@class="rank"]/text()')
    votes = tree.xpath('//span[@class="score"]/text()')
    title = tree.xpath('//td[@class="title"]/text()')
    posterUrls = appendUrl( filter1of3(tree.xpath('//td[@class="subtext"]/a/@href')) ) 
    posterName = filter1of3( tree.xpath('//td[@class="subtext"]/a/text()') )
    permaLinks = appendUrl( filter2of3(tree.xpath('//td[@class="subtext"]/a/@href')) ) #post link tree.xpath('//td[@class="title"]/a/@href')[:-1]
    
    posts = [typePost , permaLinks, votes, intro , posterName,posterUrls]
    posts = map(list, zip(*posts))
    return posts



def filterPosts(posts,start,end):
    return posts[int(start)-1:int(end)]

def getCommentsFromPost(post):
    comments = [] # comment, permalink, - , 150char, posrter, posterUrl
    pageHtml = loadPageUrl(post[1])
    tree = html.fromstring(pageHtml)
    links = tree.xpath('//span[@class="comhead"]/a/@href')
    permalinks = [URL_BASE+links[i] for i in range(len(links)) if i%2 == 1]
    userlinks = [URL_BASE+links[i] for i in range(len(links)) if i%2 == 0]
    commentsText = []
    commentsAuthor = []
    for c in tree.xpath('//td[@class="default"]'):
        text = c.text_content().split('\n')
        aux = '\n'.join( text[1:])[:-5]
        commentsText.append(aux[:min(len(aux),150)])
        commentsAuthor.append(text[0].split(' ')[0])

    typeRow = ["comment"] * len(permalinks)    
    points = [" "] * len(permalinks)    
    comments = [ typeRow , permalinks,points, commentsText , commentsAuthor,userlinks]
    comments = map(list, zip(*comments))
    return comments





def expandCommentsFromPosts(allPosts):
    combined = []
    for p in allPosts:
        combined.append(p)
        comments = getCommentsFromPost(p)
        for c in comments:
            combined.append(c)

    return combined


#==========================================================================
# MAIN PROGRAM
#==========================================================================

# Read and parse the command line flags
(options,args) = parseCommandLineFlags()
debug(5, 'Options = %s' % options)
debug(5, 'Arguments = %s' % args)



# If a read file is provided, read it.
if options.readfile:
    inputs = readFile(options.readfile)
    debug(1, '{0} item(s) found in the file {1}.'.format(len(inputs),options.readfile) )

# Else look to see if the user specified any line arguments
elif args != []:
    inputs = args
    debug(1, '{0} item(s) found in the arguments.'.format( len(inputs) ) )

# Otherwise read from stdin for data being piped in from another command
else:
    inputs = []
    generator = (line.strip() for line in sys.stdin)
    for line in generator:
        if line != '':
            inputs.append(line)
    debug(1, '{0} item(s) found on stdin.'.format( len(inputs) ) )


##### The majority of your code will probably replace the next line #####
startPost = inputs[0]
endPost = inputs[1]

startPage = getPageFromPostId(startPost)
endPage =  getPageFromPostId(endPost)

pagesUrls = createPageUrls(startPage,endPage)

allPosts = []
for pageUrl in pagesUrls:
    page = loadPageUrl(pageUrl)
    pagePosts = scrapeAllPosts(page)
    allPosts = allPosts + pagePosts
allPosts = filterPosts(allPosts,startPost,endPost)
    
postsAndComments = expandCommentsFromPosts(allPosts)

# print postsAndComments
outputs = postsAndComments    # inputs

if len(inputs) == 3:
    myfile = open(inputs[2], 'wb')
    wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
    wr.writerows(outputs)

# If an output file is specified, write to it.
if options.writefile:
    writeFile(options.writefile, outputs)

# Otherwise write it to stdout
else:
    for line in outputs:
        print(line)