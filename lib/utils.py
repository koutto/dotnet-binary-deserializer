from colorama import *
import os
import os.path
import shutil
try:
    import pygments
    import pygments.lexers
    import pygments.formatters
except ImportError:
    print 'Pygments not found, no XML syntax highlighting available'
    pygments = None



class PrintUtils(object):

	@staticmethod
	def hexdump(src, length=16):
		FILTER = ''.join([(len(repr(chr(x))) == 3) and chr(x) or '.' for x in range(256)])
		lines = []
		for c in xrange(0, len(src), length):
			chars = src[c:c+length]
			hex = ' '.join(["%02x" % ord(x) for x in str(chars)])
			printable = ''.join(["%s" % ((ord(x) <= 127 and FILTER[ord(x)]) or '.') for x in str(chars)])
			lines.append("%04x  %-*s  %s\n" % (c, length*3, hex, printable))
		print ''.join(lines)

	@staticmethod
	def print_xml_highlighted(xml):
		if pygments is not None:
			print pygments.highlight(xml, 
				                     pygments.lexers.get_lexer_by_name('XML'), 
				                     pygments.formatters.get_formatter_by_name('terminal'))
		else:
			print xml


	@staticmethod
	def print_title(title):
		print Style.BRIGHT + Fore.YELLOW + title + Style.RESET_ALL

	@staticmethod
	def print_error(reason):
		print Style.BRIGHT + Fore.RED + '[!] ' + reason.strip() + Style.RESET_ALL

	@staticmethod
	def print_warning(reason):
		print Style.BRIGHT + Fore.YELLOX + '[!] ' + Style.RESET_ALL + reason.strip()

	@staticmethod
	def print_success(reason):
		print Style.BRIGHT + Fore.GREEN + '[+] ' + Style.NORMAL + reason.strip() + Style.RESET_ALL

	@staticmethod
	def print_info(info):
		print Style.BRIGHT + "[~] " + Style.RESET_ALL + info.strip() 

	@staticmethod
	def print_delimiter():
		print '-'*80



class FileUtils(object):

	@staticmethod
	def write_to_file(filename, data):
		try:
			with open(filename, 'w') as f:
				f.write(data)
			return True
		except Exception as e:
			return False



class Net7BitInteger(object):

	@staticmethod
	def decode7bit(bytes):
	    bytes = list(bytes)
	    value = 0
	    shift = 0
	    nb_bytes = 0
	    while True:
	    	nb_bytes += 1
	        byteval = ord(bytes.pop(0))
	        if(byteval & 128) == 0: break
	        value |= ((byteval & 0x7F) << shift)
	        shift += 7
	    return ((value | (byteval << shift)), nb_bytes)

	@staticmethod
	def encode7bit(value):
	    temp = value
	    bytes = ""
	    while temp >= 128:
	        bytes += chr(0x000000FF & (temp | 0x80))
	        temp >>= 7
	    bytes += chr(temp)
	    return bytes


