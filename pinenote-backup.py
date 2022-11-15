#!/usr/bin/python

import subprocess
import re
import time
import argparse
import os
import sys
import signal

class RkDevelopTool:
  def __init__(self) -> None:
    {}

  def error(self, message : str) -> None:
    print(message)

  def getFlashInfo(self, printResult : bool =True) -> bool:
    flashInfo = None
    try:
      flashInfo = subprocess.Popen(['rkdeveloptool', 'read-flash-info'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
      self.error("Unable to run rkdeveloptool read-flash-info, is it in your $PATH?")
      return False
    stdout, stderr = flashInfo.communicate()
    if flashInfo.returncode != 0:
      self.error("FAILED: To have rkdeveloptool perform read-flash-info, maybe it a different version\n")
      self.error(stdout.decode('utf-8'))
      return False
    
    result = stdout.decode('utf-8')
    self.size = None
    self.sectors = None
    self.blockSize = None
    self.pageSize = None
    for line in result.splitlines():
      match = re.match("\s*Flash\s+Size:\s+([0-9]+)\s*MB", line)
      if match:
        self.size = int(match.group(1))

      match = re.match("\s*Flash\s+Size:\s+([0-9]+)\s*Sectors", line)
      if match:
        self.sectors = int(match.group(1))

      match = re.match("\s*Block\s+Size:\s+([0-9]+)\s*KB", line)
      if match:
        self.blockSize = int(match.group(1))

      match = re.match("\s*Page\s+Size:\s+([0-9]+)\s*KB", line)
      if match:
        self.pageSize = int(match.group(1))


    if self.size == None or self.sectors == None or self.blockSize == None or self.pageSize == None:
      self.error("Failed to parse the output\n")
      self.error(result)
      return False

    if printResult:
      print("Detected:")
      print("Flash Size   : {:d} MB".format(self.blockSize))
      print("Flash Sectors: {:d}".format(self.sectors))
      print("Block Size   : {:d} not kB".format(self.blockSize))
      print("Page Size    : {:d} kB".format(self.pageSize))


    if self.size != self.sectors*self.blockSize/1024/1024:
      self.error("Flash numbers do not add up!")
      return False

    return True

  def readFlashBlock(self, startSector : int, size : int, filename : str):
    try:
      read = subprocess.Popen(['rkdeveloptool', 'read', str(startSector), str(size), filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
      self.error("No longer able to run rkdeveloptool, this is odd")
      return False
    stdout, stderr = read.communicate()
    if read.returncode != 0:
      self.error("FAILED: To have rkdeveloptool perform read\n")
      self.error(stdout.decode('utf-8'))
      return False
    return True

def secondsToString(seconds : int) -> str:
  if seconds <= 60:
    return "{:d}s".format(seconds)
  if seconds <= 3600:
    minutes = int(seconds / 60)
    seconds = int(seconds % 60)
    return "{:d}m:{:d}s".format(minutes, seconds)
  else:
    hours = int(seconds/3600)
    seconds = int(seconds % 3600)
    minutes = int(seconds / 60)
    seconds = int(seconds % 60)
    return "{:d}h:{:d}m:{:d}s".format(hours, minutes, seconds)

parser = argparse.ArgumentParser(description="A script for backing up a PineNote, may be useful for other devices using that can be accessed with rkdeveloptool")
parser.add_argument('-b', '--block_size', default=1024*1024*1024, type=int, help="The max number of bytes to get at once, larger partitions/disks will be broken up into blocks according to this size to circumvent the 2GB limit")
parser.add_argument('-t', '--type', required=True, choices=['partitions', 'disk'], help="The type of backup, partitions=attempt to get the individual partitions in separate files, disk=grap every byte including the partition table")

args = parser.parse_args()

blockSize = args.block_size
type = args.type

running_ = True

def handler(signum, frame):
  global running_
  print("\nDetected Ctrl-C, your PineNote may become stuck and need to be powered off and placed in download mode again")
  print("Not all data have been downloaded")
  running_ = False

signal.signal(signal.SIGINT, handler)

dut = RkDevelopTool()

startTime = time.time()
if type=='disk':
  if dut.getFlashInfo():
    block = 0
    index = 0
    bytes = dut.blockSize*dut.sectors
    while(index<bytes):
      progress = index * 100 / bytes
      etaString = "N.A."
      if (index != 0):
        timePassed = time.time() - startTime
        totalSeconds = bytes/(index/timePassed)
        secondsRemaining = totalSeconds - timePassed
        if secondsRemaining < 0:
          secondsRemaining = 0
        etaString = secondsToString(secondsRemaining)

      if index % dut.blockSize != 0:
        print("Internal error invalid offset!?")
        os._exit(1)
      startSector = int(index/dut.blockSize)

      size = bytes - index
      if size > blockSize:
        size = blockSize
      size = int(size/dut.blockSize)*dut.blockSize
      
      print("Reading {:d} bytes from sector {:d} done: {:.0f}% eta. {:s}".format(size, startSector, progress, etaString))
      sys.stdout.flush()
      filename = "diskimage.{:04d}".format(block)
      if not dut.readFlashBlock(startSector, size, filename):
        print("An error occurred while reading data")
        os._exit(1)      
  
      index += size
      block += 1
  else:
    print("!!! An error was encounterd !!!")
    os._exit(1)