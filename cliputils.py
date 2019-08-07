import sys
import struct
import os

CSF_CHUNK = b'CSFCHUNK'
CHUNK_HEADER = b'CHNKHead'
CHUNK_EXTERNAL = b'CHNKExta'
CHUNK_SQLITE = b'CHNKSQLi'
CHUNK_FOOTER = b'CHNKFoot'

BLOCK_DATA_BEGIN_CHUNK = b'\x00B\x00l\x00o\x00c\x00k\x00D\x00a\x00t\x00a\x00B\x00e\x00g\x00i\x00n\x00C\x00h\x00u\x00n\x00k'
BLOCK_DATA_END_CHUNK = b'\x00B\x00l\x00o\x00c\x00k\x00D\x00a\x00t\x00a\x00E\x00n\x00d\x00C\x00h\x00u\x00n\x00k'
BLOCK_STATUS = b'\x00B\x00l\x00o\x00c\x00k\x00S\x00t\x00a\x00t\x00u\x00s'
BLOCK_CHECK_SUM = b'\x00B\x00l\x00o\x00c\x00k\x00C\x00h\x00e\x00c\x00k\x00S\x00u\x00m'

clip_header_spec = struct.Struct('>8sQQ')
chunk_header_spec = struct.Struct('>8sQ')
external_header_spec = struct.Struct('>Q40sQ')
block_test_spec = struct.Struct('>II')
uint_spec = struct.Struct('>I')
block_header_spec = struct.Struct('>I12xI')

def __read(struct, infile, pos):
    buff = infile.read(struct.size)
    data = struct.unpack_from(buff)
    return (data, pos + struct.size)

def __pipe_file(outdir, filename, infile, length):
    outfile = open(os.path.join(outdir, filename), 'wb')
    outfile.write(infile.read(length))
    outfile.close()

def split_clip(path, outdir, options):
    basedir, filename = os.path.split(path)
    ext_index = filename.rfind('.clip')
    if ext_index < 0:
        return
    without_ext = filename[:ext_index]
    outdir = os.path.join(basedir, without_ext)
    os.makedirs(outdir, exist_ok=True)
    infile = open(path, 'rb')
    pos = 0
    data, pos = __read(clip_header_spec, infile, pos)
    _, filesize, _ = data
    while pos < filesize:
        oldpos = pos
        data, pos = __read(chunk_header_spec, infile, pos)
        chunk_type, length = data
        if options.verbose:
            print('{0}: {1} ({2})'.format(oldpos, chunk_type.decode('UTF-8'), length))
        if chunk_type == CHUNK_HEADER:
            __pipe_file(outdir, 'header', infile, length)
        if chunk_type == CHUNK_SQLITE:
            __pipe_file(outdir, without_ext + '.sqlite3', infile, length)
        elif chunk_type == CHUNK_EXTERNAL:
            data, pos2 = __read(external_header_spec, infile, pos)
            _, external_id, data_size = data
            external_id_str = external_id.decode('UTF-8')
            if options.verbose:
                print('  {0} ({1})'.format(external_id_str, data_size))
            if options.blockdata:
                __read_blockdata(infile, pos2, length, external_id_str, outdir, options)
                infile.seek(pos2)
            else:
                __pipe_file(outdir, external_id_str, infile, data_size)
        pos = infile.seek(pos + length)
    infile.close()

def __read_blockdata(infile, pos, length, external_id, outdir, options):
    end_pos = pos + length
    while pos < end_pos:
        test_data, pos = __read(block_test_spec, infile, pos)
        a, b = test_data
        if b == 4325484: # b'\x00B\x00l':
            str_length = a
            pos = infile.seek(pos - 4)
        else:
            str_length = b
            data_length = a
        bd_id = infile.read(str_length * 2)
        pos += str_length * 2
        if bd_id == BLOCK_DATA_BEGIN_CHUNK:
            if options.verbose:
                print('  {0}'.format(infile.peek(20)[:20].hex()))
            data, pos = __read(block_header_spec, infile, pos)
            block_index, not_empty = data
            if not_empty > 0:
                data, pos = __read(uint_spec, infile, pos)
                block_length = data[0]
                if options.verbose:
                    print('  BlockDataBeginChunk {0} ({1})'.format(block_index, block_length))
                __pipe_file(outdir, '{0}.{1}'.format(external_id, block_index), infile, block_length)
                pos += block_length
            else:
                if options.verbose:
                    print('  BlockDataBeginChunk {0} (empty)'.format(block_index))
        elif bd_id == BLOCK_DATA_END_CHUNK:
            if options.verbose:
                print('  BlockDataEndChunk')
        elif bd_id == BLOCK_STATUS:
            if options.verbose:
                print('  BlockStatus')
            pos = infile.seek(pos + 28)
        elif bd_id == BLOCK_CHECK_SUM:
            if options.verbose:
                print('  BlockCheckSum')
            pos = infile.seek(pos + 28)
            return
        else:
            print('Unknown Block: {0}'.format(str_length))
            return

def __main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true', help='print verbose log')
    parser.add_argument('-s', '--split', action='store_true', help='split operation')
    parser.add_argument('-m', '--merge', action='store_true', help='merge operation')
    parser.add_argument('--blockdata', action='store_true', help='split blockdata')
    targets = parser.add_argument_group('targets')
    targets.add_argument('-c', '--clip', type=str, help='clip file')
    targets.add_argument('-d', '--dir', type=str, help='splitted data direcotry')
    args = parser.parse_args()
    def err(msg):
        print(msg)
        parser.print_usage()
    if args.split and not args.clip:
        err('You have to specify -c|--clip.')
        return
    if args.merge and not args.dir:
        err('You have to specify -d|--dir.')
        return
    if not (args.split or args.merge):
        err('You have to specify -s|--split or -m|--merge.')
        return
    if args.split:
        split_clip(args.clip, args.dir, args)
    if args.merge:
        print('Merge operation is not supported.')

if __name__ == '__main__':
    __main()

