import urllib2

import boto3

BUF_SZ = 1024768


def handler(event, context):
    s3 = boto3.resource('s3')
    url = event["URL"]
    parsed = urllib2.urlparse.urlparse(url)
    response = s3.Object(parsed.netloc, parsed.path.lstrip('/')).get()

    linecount = bytes = 0
    contents = response['Body'].read(BUF_SZ)
    while contents:
        bytes += len(contents)
        linecount += contents.count('\n')
        contents = response['Body'].read(BUF_SZ)
    return {
        'url': event["URL"],
        'lines': linecount,
        'bytes': bytes
    }
