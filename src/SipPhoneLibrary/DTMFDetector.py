##############################################
## Modified by: David Luu
## Last modified: 10/24/2010
##
## NOTE: website below incorrect, updated one is
## http://johnetherton.com/projects/pys60-dtmf-detector
##
## Original code info:
##
## last updated: 2/2/2007
## 
## This is written by John Etherton - john@johnetherton.com
## http://johnetherton.com/programming/DTMFdetect/
##
##
## Please send me any questions or comments about this code.
## I made this so I could do DTMF detection with python on a 
## Nokia Series 60 phone. So that's all it really does. I made it as
## as quickly as I could. This is my first attempt at making a general,
## reusable library for PyS60.
##
## LICENSE STUFF:
## This code is released to the public for any use. I wish I knew which
## license that is but I don't know. I should probably find out.
##
## This is code is offered as is with out any warranty. If it breaks
## and does something bad, don't sue me. I have tested it to the 
## best of my ability, but I have no doubt that it has numerous
## faults
##
## The Goertzel algorithm used in this script was shamelessly stolen
## from this wikipedia entry: http://en.wikipedia.org/wiki/Goertzel_algorithm
## All the code not given in that entry I wrote myself. 
##
## IMPORTANT:
## for this to work with PyS60 1.3.17 I had to install the wave.py
## and chunk.py files from my python 2.2 installation onto
## the phone as libraries.
##
## Usage example:
##
## -Assume we have a single channel 16 bit, 8000hz file "audioFile.wav"
## -that was recorded on a phone when someone pressed 8,3,3,4,5
## CODE:
##        from DTMFdetector import DTMFdetector
##        dtmf = DTMFdetector() 
##        data = dtmf.getDTMFfromWAV("audioFile.wav")
##        print data
## OUTPUT:
##        "83345"
## 
## It's that simple
##
## Oh and I can't spell so please forgive all my mistakes
##############################################

import chunk
import wave
import struct
import math


###############################################
## This class is used to detect DTMF tones in a WAV file
##
## Currently this only works with uncompressed .WAV files
## encoded 16 bits per channel, one channel, at 8000 hertz.
## I know if I tried I could make this so it'd work with 
## other sampling rates and such, but this is how PyS60 records
## audio and I've got a bunch of other things to work on right 
## now. If you want to add this functionality please go ahead
## and do it
class DTMFdetector(object):


    ###########################################
    ## The default constructor
    ##
    ## initializes the instance variables
    ## pre-calculates the coefficients
    def __init__(self):

        #DEFINE SOME CONSTANTS FOR THE 
        #GOERTZEL ALGORITHM
        self.MAX_BINS = 8
        self.GOERTZEL_N = 92
        self.SAMPLING_RATE = 8000

        #the frequencies we're looking for
        self.freqs = [697, 770, 852, 941, 1209, 1336, 1477, 1633]

        #the coefficients
        self.coefs = [0, 0, 0, 0, 0, 0, 0, 0]

        self.reset()
        
        self.calc_coeffs()


    ###########################################
    ## Custom constructor, added for support
    ## of additional audio file formats
    ##
    ## initializes the instance variables
    ## pre-calculates the coefficients
    def __init__(self,pfreq,pdebug):

        #DEFINE SOME CONSTANTS FOR THE 
        #GOERTZEL ALGORITHM
        self.MAX_BINS = 8

        if pfreq == 16000:
            #16kHz
            self.GOERTZEL_N = 210
            self.SAMPLING_RATE = 16000
        else:
            #8kHz default
            self.GOERTZEL_N = 92
            self.SAMPLING_RATE = 8000

        #the DTMF frequencies we're looking for
        self.freqs = [697, 770, 852, 941, 1209, 1336, 1477, 1633]

        #the coefficients
        self.coefs = [0, 0, 0, 0, 0, 0, 0, 0]

        self.reset()
        
        self.calc_coeffs()

        self.debug = pdebug

    
    ###########################################
    ## This will reset all the state of the detector
    def reset(self):
        #the index of the current sample being looked at
        self.sample_index = 0
        
        #the counts of samples we've seen
        self.sample_count = 0

        #first pass
        self.q1 = [0, 0, 0, 0, 0, 0, 0, 0]

        #second pass
        self.q2 = [0, 0, 0, 0, 0, 0, 0, 0]

        #r values
        self.r = [0, 0, 0, 0, 0, 0, 0, 0]
        
        #this stores the characters seen so far
        #and the times they were seen at for
        #post, post processing
        self.characters = []
        
        #this stores the final string of characters
        #we believe the audio contains
        self.charStr = ""

    ###########################################
    ## Post testing for algorithm
    ## figures out what's a valid signal and what's not
    def post_testing(self):
        row = 0
        col = 0
        see_digit = 0
        peak_count = 0
        max_index = 0
        maxval = 0.0
        t = 0
        i = 0
        msg = "none"
        
        row_col_ascii_codes = [["1", "2", "3", "A"],["4", "5", "6", "B"],["7", "8", "9", "C"],["*", "0", "#", "D"]]
        
        #Find the largest in the row group.
        for i in range(4):
            if self.r[i] > maxval:
                maxval = self.r[i]
                row = i
                
        #Find the largest in the column group.
        col = 4
        maxval = 0
        for i in range(4,8):
            if self.r[i] > maxval:
                maxval = self.r[i]
                col = i
                
        #Check for minimum energy
        if self.r[row] < 4.0e5:
            msg = "energy not enough"
        elif self.r[col] < 4.0e5:
            msg = "energy not enough"
        else:
            see_digit = True

            #Normal twist
            if self.r[col] > self.r[row]:        
                max_index = col
                if self.r[row] < (self.r[col] * 0.398):
                    see_digit = False
            #Reverse twist
            else:
                max_index = row
                if self.r[col] < (self.r[row] * 0.158):
                    see_digit = False
                    
            
            #signal to noise test
            #AT&T states that the noise must be 16dB down from the signal.
            # Here we count the number of signals above the threshold and
            #there ought to be only two.
            if self.r[max_index] > 1.0e9:
                t = self.r[max_index] * 0.158
            else:
                t = self.r[max_index] * 0.010
            
            peak_count = 0
            
            for i in range(8):
                if self.r[i] > t:
                    peak_count = peak_count + 1
            if peak_count > 2:
                see_digit = False
                if self.debug:
                    print "peak count is to high: ", peak_count
            
            if see_digit:
                if self.debug:
                    print row_col_ascii_codes[row][col-4] #for debugging
                #stores the character found, and the time in the file in seconds in which the file was found
                self.characters.append( (row_col_ascii_codes[row][col-4], float(self.sample_index) / float(self.SAMPLING_RATE)) )
                

    ###########################################
    ## This takes the number of characters found and such and 
    ## figures out what's a distinct key press.
    ##
    ## So say you pressed 5,3,2,1,1
    ## The algorithm sees 555553333332222221111111111111
    ## Cleaning up gives you 5,3,2,1,1
    def clean_up_processing(self):
        #this is nothing but a fancy state machine
        #to get a valid key press we need 
        MIN_CONSECUTIVE = 2
        #characters in a row
        #with no more than
        MAX_GAP = 0.3000
        #seconds between each consecutive characters
        #otherwise we'll think they've pressed the same
        #key twice
        
        self.charStr = ""
        
        currentCount = 0
        lastChar = ""
        lastTime = 0
        charIndex = -1
        
        for i in self.characters:            
            
            charIndex+=1
            currentChar = i[0]
            currentTime = i[1]
            timeDelta = currentTime - lastTime
            
            if self.debug:
                print "curr char:", currentChar, "time delta:", timeDelta #for debugging
            
            #check if this is the same char as last time
            if lastChar == currentChar:
                currentCount+=1
            else:
                #some times it seems we'll get a stream of good input, then some erronous input
                #will pop-up just once. So what we're gonna do is peak ahead here and see what
                #if it goes back to the pattern we're getting and then decide if we should
                # let it go, stop th whole thing
                # Make sure we can look ahead
                if len(self.characters) > (charIndex + 2):
                    if (self.characters[charIndex + 1][0] == lastChar) and (self.characters[charIndex + 2][0] == lastChar):
                        #forget this every happened
                        lastTime = currentTime
                        continue
                
                #check to see if we have a valid key press on our hands
                if currentCount >= MIN_CONSECUTIVE:
                        self.charStr+=lastChar                        
                        currentCount = 1
                        lastChar = currentChar
                        lastTime = currentTime
                        continue
            
            #check to see if we have a big enough gap to make us think we've
            #got a new key press            
            if timeDelta > MAX_GAP:
                #so de we have enough counts for this to be valid?
                if (currentCount - 1) >= MIN_CONSECUTIVE:
                        self.charStr+=lastChar
                currentCount = 1
                        
                
            
            
            lastChar = currentChar
            lastTime = currentTime
    
        #check the end of the characters        
        if currentCount >= MIN_CONSECUTIVE:
                        self.charStr+=lastChar

    ###########################################
    ## the Goertzel algorithm
    ## takes in a 16 bit signed sample
    def goertzel(self, sample):
        q0 = 0
        i = 0
        
        self.sample_count += 1
        self.sample_index += 1
        
        for i in range(self.MAX_BINS):
            q0 = self.coefs[i] * self.q1[i] - self.q2[i] + sample
            self.q2[i] = self.q1[i]
            self.q1[i] = q0
            
        if self.sample_count == self.GOERTZEL_N:
            for i in range(self.MAX_BINS):
                self.r[i] = (self.q1[i] * self.q1[i]) + (self.q2[i] * self.q2[i]) - (self.coefs[i] * self.q1[i] * self.q2[i])
                self.q1[i] = 0
                self.q2[i] = 0
            self.post_testing()
            self.sample_count = 0
            


    ###########################################
    ## calculate the coefficients ahead of time
    def calc_coeffs(self):
        for n in range(self.MAX_BINS):
            self.coefs[n] = 2.0 * math.cos(2.0 * math.pi * self.freqs[n] / self.SAMPLING_RATE)
            #print "coefs", n, "=", self.coefs[n] #for debugging

        


    ###########################################
    ## this will take in a file name of a WAV file and return
    ## a string that contains the characters that were detected
    ## so if youre WAV file has the DTMFs for 5,5,5,3 then the string
    ## it returns will be "5553"
    def getDTMFfromWAV(self, filename):
        
        self.reset() #reset the current state of the detector
        
        file = wave.open(filename)

        #print file.getparams()
        totalFrames = file.getnframes()
    
        count = 0


        while totalFrames != count:    
            raw = file.readframes(1)
            (sample,) = struct.unpack("h", raw)
            self.goertzel(sample)
            count = count + 1
        
        file.close()
        
        self.clean_up_processing()
        
        return self.charStr




