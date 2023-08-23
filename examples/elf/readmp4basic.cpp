#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <algorithm>

// http://code.activestate.com/recipes/496984-iterate-over-mp4-atoms/
// https://developer.apple.com/library/mac/#documentation/QuickTime/QTFF/QTFFChap2/qtff2.html#//apple_ref/doc/uid/TP40000939-CH204-SW1
// http://www.jiscdigitalmedia.ac.uk/audio/advice/aac-audio-and-the-mp4-media-format/#aac-and-mpeg


using namespace std;


int readAtomLength(ifstream& infile) {
    char lenbuf[4];
    infile.read(lenbuf, 4);
    if (!infile) return -1;
    int len = (unsigned char(lenbuf[0]) << 24) + 
        (unsigned char(lenbuf[1]) << 16) + 
        (unsigned char(lenbuf[2]) << 8) + 
         unsigned char(lenbuf[3]);
    return len;
}

string readChunkType(ifstream& infile) {
    char data[4];

    infile.read(data, 4);
    string chunktype;
    chunktype = chunktype + data[0] + data[1] + data[2] + data[3];
    return chunktype;
}

int main(int argc, char *argv[])
{
    vector<string> args(argv, argv+argc);

    if (args.size() != 2) {
        cout << "Usage: mp4reader <filename>" << endl;
        return 1;
    }

    string filename = args.at(1);

    ifstream infile(filename.c_str());

    if (!infile) {
        cout << "Unable to open " << filename << endl;
        return 1;
    }

    while (infile) {
        // process an atom
        int len = readAtomLength(infile);
        if (len == -1) break;

        string chunktype = readChunkType(infile);
        cout << "Chunk " << chunktype << " has length " << len << endl;

        // skip to next atom
        infile.seekg(len - 8, ios_base::cur);
    }

    return 0;
}

