using System;
using System.IO;

// Reads MP3 tags 
// See http://id3.org/id3v2.3.0 for MP3 tag spec
class Program
{
    static void Main(string[] args)
    {
        if (args.Length != 1)
        {
            Console.WriteLine("Usage: mp3readtag <mp3filename>");
            Environment.Exit(1);
        }

        string filename = args[0];
        Console.WriteLine("Reading " + filename);

        FileStream fs = File.Open(filename, FileMode.Open);
        using (BinaryReader br = new BinaryReader(fs))
        {
            byte[] tag = new byte[3];
            byte[] version = new byte[2];
            byte[] flags = new byte[1];
            byte[] size = new byte[4];

            // Read Tag Header

            // ID3v2/file identifier   "ID3"
            // ID3v2 version           $03 00
            // ID3v2 flags             % abc00000
            // ID3v2 size              4 * % 0xxxxxxx

            br.Read(tag, 0, tag.Length);
            br.Read(version, 0, version.Length);
            br.Read(flags, 0, flags.Length);
            br.Read(size, 0, size.Length);

            string fileIdentifier = BytesToString(tag);
            if (fileIdentifier != "ID3")
            {
                Console.WriteLine(filename + " does not contain ID3 tags.");
                Environment.Exit(1);
            }

            int frameNo = 0;
            int bytesToRead = BytesToSize(size);
            while (bytesToRead > 0)
            {
                // Read Frame Header

                // Frame ID       $xx xx xx xx (four characters)
                // Size           $xx xx xx xx
                // Flags          $xx xx

                byte[] frameIdBytes = new byte[4];
                byte[] frameSizeBytes = new byte[4];
                byte[] frameFlags = new byte[2];
                br.Read(frameIdBytes, 0, frameIdBytes.Length);
                br.Read(frameSizeBytes, 0, frameSizeBytes.Length);
                br.Read(frameFlags, 0, frameFlags.Length);

                int frameSize = BytesToSize(frameSizeBytes);
                Console.WriteLine("Frame #" + frameNo);
                Console.WriteLine("Frame Data Size : " + frameSize);

                string frameId = BytesToString(frameIdBytes);
                Console.WriteLine("Frame ID: " + frameId);

                // Read Frame Body

                if (frameId[0] == 'T')
                {
                    // a text frame
                    int encoding = br.Read();

                    // Ignore encoding and hope for the best(!)

                    byte[] body = new byte[frameSize - 1];
                    br.Read(body, 0, body.Length);
                    Console.WriteLine("Data: " + BytesToString(body));
                }
                else
                {
                    // some other type of frame 
                    byte[] body = new byte[frameSize];
                    br.Read(body, 0, body.Length);

                }
                Console.WriteLine("------------------------------------");

                bytesToRead -= frameSize + 10;
                ++frameNo;
            }

        }

    }

    // Converts an MP3 length field to int
    // "The ID3v2 tag size is encoded with four bytes where 
    // the most significant bit (bit 7) is set to zero in every byte, making a total of 28 bits."
    // See http://id3.org/id3v2.3.0#ID3v2_header

    private static int BytesToSize(byte[] sizeBytes)
    {
        return sizeBytes[0] << 21 | sizeBytes[1] << 14 | sizeBytes[2] << 7 | sizeBytes[3];
    }

    // Converts an array of bytes to a string
    private static string BytesToString(byte[] data)
    {
        string result = "";
        foreach (byte b in data)
        {
            result += (char)b;
        }
        return result;
    }

}
