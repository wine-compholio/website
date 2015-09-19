#!/usr/bin/python2
import sys
import os
import errno

from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl

def loadTemplate():
    with open('_template/index.html', 'r') as f:
        template_content = f.read()

    parts = template_content.split("@@CONTENT@@")
    if len(parts) != 2:
        raise RuntimeError("Unable to split template based on @@CONTENT@@")

    return parts

def generateStaticSites(template, destdir):
    for filename in os.listdir("_source/"):
        full_path = os.path.join("_source", filename)
        if not os.path.isfile(full_path):
            continue

        with open(full_path, 'r') as f:
            content = f.read()

        with open(os.path.join(destdir, filename), 'wb') as f:
            f.write("%s%s%s" % (template[0], content, template[1]))

def generateNewsPost(title, date, content, extra):
    return """
        <div class="post">
                <h2 class="title">%s</h2>
                <p class="meta"><span class="author">Wine Staging Team</span>&nbsp;-&nbsp<span class="date">%s</span></p>
                <div class="entry">
                    %s
                    %s
                </div>
            </div>
    """ % (title, date, content, extra)

def startAtomFeed(filename, date):
    generator = XMLGenerator(open(filename, 'wb'), 'utf8')

    generator.startDocument()

    generator.startElement(u'feed', AttributesImpl({u'xmlns': u'http://www.w3.org/2005/Atom'}))

    generator.startElement(u'id', AttributesImpl({}))
    generator.characters(u'http://www.wine-staging.com/news.xml')
    generator.endElement(u'id')

    generator.startElement(u'title', AttributesImpl({}))
    generator.characters(u'Wine Staging')
    generator.endElement(u'title')

    generator.startElement(u'updated', AttributesImpl({}))
    generator.characters(date.decode('utf8'))
    generator.endElement(u'updated')

    generator.startElement(u'link', AttributesImpl({u'rel': u'self', u'href': u'/news.xml'}))
    generator.endElement(u'link')

    generator.startElement(u'link', AttributesImpl({u'rel': u'alternate', u'type': u'text/html', u'href': u'/news.html'}))
    generator.endElement(u'link')

    return generator

def writeNewsAtomEntry(generator, title, date, filename, summary):
    generator.startElement(u'entry', AttributesImpl({}))

    generator.startElement(u'title', AttributesImpl({}))
    generator.characters(title.decode('utf8'))
    generator.endElement(u'title')

    generator.startElement(u'link', AttributesImpl({u'rel': u'alternate', u'href': u'/news/%s' % filename.decode('utf8')}))
    generator.endElement(u'link')

    generator.startElement(u'id', AttributesImpl({}))
    generator.characters(u'http://www.wine-staging.com/news/%s' % filename.decode('utf8'))
    generator.endElement(u'id')

    generator.startElement(u'updated', AttributesImpl({}))
    generator.characters(filename[0:10].decode('utf8'))
    generator.endElement(u'updated')

    generator.startElement(u'summary', AttributesImpl({u'type': u'html'}))
    generator.characters(summary)
    generator.endElement(u'summary')

    generator.endElement(u'entry')

def endAtomFeed(generator):
    generator.endElement(u'feed')

    generator.endDocument()

def try_mkdir(dir):
    try:
        os.mkdir(dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def read_news(path):
    headers = {}
    with open(path, 'r') as f:

        # read headers until we encounter the first empty line
        while True:
            line = f.readline().strip()
            if line == "": break
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

        # remaining content
        content = f.read()
    return headers, content

def generateNewsSites(template, destdir):
    overview = []
    files = []

    try_mkdir(os.path.join(destdir, "news"))

    # Enumerate news
    for filename in os.listdir("_source/news"):
        full_path = os.path.join("_source/news", filename)
        if os.path.isfile(full_path): files.append(filename)
    files.sort(reverse=True)

    generator = startAtomFeed(os.path.join(destdir, "news.xml"), files[0][0:10])

    for filename in files:
        full_path = os.path.join("_source/news", filename)

        headers, content = read_news(full_path)
        if "title" not in headers or "date" not in headers:
            raise RuntimeError("News %s is missing either missing title or header" % filename)

        preview    = content.split("<!--PREVIEW-->", 1)[0]
        title_link = "<a href=\"/news/%s\">%s</a>" % (filename, headers["title"])
        read_more  = "<p><a href=\"/news/%s\">Read more</a></p>" % (filename)
        overview.append(generateNewsPost(title_link, headers["date"], preview, read_more))

        content = generateNewsPost(headers["title"], headers["date"], content, "")
        with open(os.path.join(destdir, "news", filename), 'wb') as f:
            f.write("%s%s%s" % (template[0], content, template[1]))

        writeNewsAtomEntry(generator, headers["title"], headers["date"], filename, preview)

    endAtomFeed(generator)

    with open(os.path.join(destdir, "news.html"), 'wb') as f:
        f.write("%s%s%s" % (template[0], "\n".join(overview), template[1]))

if __name__ == '__main__':
    destdir  = "output"
    template = loadTemplate()
    generateStaticSites(template, destdir)
    generateNewsSites(template, destdir)
