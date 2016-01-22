from http import *
# Header
print('header from parse line')
header = Header()
line = 'Name: 1, 2, 3'
header.ParseLine(line)
print(header)
print('header from init')
header = Header('Name', '1')
print(header)
# Url
url1 = 'hello.http'
url2 = 'https://george:lucas@www.example.com:1234/yene.html?yolo#field=green'
url3 = 'https://george:lucas@www.example.com:1234/yene.html'
url = Url()
url.ParseLine(url1)
print(url)
url = Url()
url.ParseLine(url2)
print(url)
url = Url()
url.ParseLine(url3)
print(url)
# Version
version = Version(1.1)
print(version)
version = Version()
version.ParseLine('HTTP/1.2')
print(version)
# Method
method = Method('PoST')
print(method)
method = Method()
method.ParseLine('get')
print(method)
