import argparse
import os
import sys
import traceback
import signal
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from lib import *


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

def signal_handler(signal, frame):
	PrintUtils.print_info('Exiting...')
	print
	sys.exit(0)


try:
    SCRIPTNAME = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPTNAME = os.path.dirname(os.path.abspath(sys.argv[0]))
    
BANNER = """
===============================================================================
                -- .NET Binary Serializer/Deserializer --
===============================================================================
  Supported encoding formats:
  - [MC-NBFX] / [MC-NBFS]  - Standard
  - [MC-NBFSE] - With in-band dictionary (StringTable) 
  (Used by WCF in netTcpBinding mode)
"""


def show_help_and_exit(parser):
	print 
	parser.print_help()
	print
	print 'Examples:'
	print '  Decode .NET binary (auto detect encoding) into XML:'
	print '    python {0} --bin2xml -f <input_netbin_filename> -o <output_filename>'.format(SCRIPTNAME)
	print
	print '  Convert XML into .NET Binary in standard encoding - format [MC-NBFS]:'
	print '    python {0} --xml2mcnbfs -f <input_xml_filename> -o <output_filename>'.format(SCRIPTNAME)
	print
	print '  Convert XML into .NET Binary using in-band dictionary / StringTable - format [MC-NBFSE]:'
	print '    python {0} --xml2mcnbfse -f <input_xml_filename> -o <output_filename>'.format(SCRIPTNAME)
	print
	sys.exit(0)



# -----------------------------------------------------------------------------
# --- Command parsing ---------------------------------------------------------
# -----------------------------------------------------------------------------
print Style.BRIGHT + BANNER + Style.RESET_ALL
print

# Command-line parsing
parser = argparse.ArgumentParser()

io = parser.add_argument_group('Input/Output')
io.add_argument('-f', help='Input file', action='store', type=str, dest='input_file', default=None)
io.add_argument('-o', help='Output file', action='store', type=str, dest='output_file', default=None)
io.add_argument('--offset', help='Force offset', action='store', type=int, dest='offset', default=0)

mode = parser.add_argument_group('Mode')
mode.add_argument('--bin2xml', help='.NET Binary to XML', action='store_true', dest='bin2xml', default=False)
mode.add_argument('--xml2bin', help='Same as --xml2mcnbfs', action='store_true', dest='xml2mcnbfs', default=False)
mode.add_argument('--xml2mcnbfs', help='XML to .NET Binary in format [MC-NBFS] (standard)', action='store_true', dest='xml2mcnbfs', default=False)
mode.add_argument('--xml2mcnbfse', help='XML to .NET Binary in format [MC-NBFSE] with in-band dictionary', action='store_true', dest='xml2mcnbfse', default=False)

option = parser.add_argument_group('Option')
option.add_argument('--no-size-prefix', help='Do not prefix in-band dictionary with its size in 7-Bit integer format (only with --xml2mcnbfse)', action='store_true', dest='nosizeprefix', default=False)

rpc = parser.add_argument_group('RPC Server - Encode/Decode .NET Binary on-the-fly')
rpc.add_argument('--rpcserver', help='Start RPC Server', action='store_true', dest='rpcserver', default=False)
rpc.add_argument('-p', '--port', help='Listening port', action='store', type=int, dest='port', default=8000)

args = parser.parse_args()


# Check input/output
if not args.rpcserver:
	if not args.input_file:
		PrintUtils.print_error('An input file must be provided')
		show_help_and_exit(parser)
	else:
		if not os.access(args.input_file.strip(), os.F_OK):
			PrintUtils.print_error('Input file ({0}) does not exist'.format(args.input_file))
			sys.exit(0)


	if args.output_file is not None:
		filename = args.output_file.strip()
		if os.access(filename, os.F_OK):
			PrintUtils.print_error('Output file ({0}) already exists, choose a new file'.format(args.output_file))
			print
			sys.exit(0)

	# Check mode
	if (not args.bin2xml and not args.xml2mcnbfs and not args.xml2mcnbfse):
		PrintUtils.print_error('A mode must be selected')
		show_help_and_exit(parser)


	if ((args.bin2xml    and args.xml2mcnbfs) or \
		(args.bin2xml    and args.xml2mcnbfse) or \
		(args.xml2mcnbfs and args.xml2mcnbfse)):
		PrintUtils.print_error('Choose one mode only')
		show_help_and_exit(parser)

	converter = Converter(args.input_file, begin_offset=args.offset)




# -----------------------------------------------------------------------------
# --- Processing --------------------------------------------------------------
# -----------------------------------------------------------------------------

if args.bin2xml:
	PrintUtils.print_title('.NET Binary --> XML')
	print 
	PrintUtils.print_info('Input file length: {0} (0x{1:x}) bytes'.format(converter.length, converter.length))
	PrintUtils.print_info('Scanning input for .NET Binary data and try to decode it...')

	if not converter.scan_input_binary():
		sys.exit(0)


elif args.xml2mcnbfs:
	PrintUtils.print_title('XML --> .NET Binary in format [MC-NBFS] (standard encoding)')
	print 
	PrintUtils.print_info('Input file length: {0} (0x{1:x}) bytes'.format(converter.length, converter.length))

	if not converter.xml_to_mcnbfs():
		sys.exit(0)


elif args.xml2mcnbfse:
	PrintUtils.print_title('XML --> .NET Binary in format [MC-NBFSE] (in-band dictionary encoding)')
	print
	PrintUtils.print_info('Input file length: {0} (0x{1:x}) bytes'.format(converter.length, converter.length))

	if not converter.xml_to_mcnbfse(args.nosizeprefix):
		sys.exit(0)


if args.rpcserver:
	try:
		server = SimpleXMLRPCServer(("", args.port), requestHandler=RequestHandler)
		server.register_introspection_functions()
		server.register_instance(RPCServer())
	except:
		PrintUtils.print_error('Error occured when trying to start RPC server. Check if port already used.')
		sys.exit(0)

	PrintUtils.print_title('RPC Server: ON - Waiting for calls...')
	print
	signal.signal(signal.SIGINT, signal_handler)
	PrintUtils.print_info('Press Ctrl+C to stop the server')
	print
	server.serve_forever()




# Output into file
if args.output_file and converter.output:
	length = len(converter.output)
	PrintUtils.print_info('Output length = {0} ({1:X}) bytes'.format(length, length))
	if FileUtils.write_to_file(args.output_file.strip(), converter.output):
		PrintUtils.print_success('Output written into file "{0}"'.format(args.output_file))
	else:
		print_error('An error occured when writing to file. Check permissions')

print