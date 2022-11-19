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
    self.flashInfoGotten = False
    self.partitions = {}
    self.totalPartitionBytes = 0

  def error(self, message : str) -> None:
    print(message)

  def getFlashInfo(self, printResult : bool =True) -> bool:
    if self.flashInfoGotten:
      return True
    flashInfo = None
    try:
      flashInfo = subprocess.Popen(['rkdeveloptool', 'read-flash-info'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
      self.error("Unable to run 'rkdeveloptool read-flash-info', is it in your $PATH?")
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

    self.flashInfoGotten = True
    return True

  def addPartitionInformation(self, skippedPartitions : list, printResult : bool, partNumber : int, name : str, startSector : int, endSector : int, byteLength : int) -> None:
    skippedText = ""
    if name in skippedPartitions:
      skippedText = " SKIPPED!"
    else:
      self.totalPartitionBytes += byteLength
      partitionInfo = {'name': name, 'startSector': startSector, 'endSector': endSector, 'byteLength': byteLength}
      self.partitions[partNumber] = partitionInfo
    if printResult:
      print("{:03d} name: {:18s} sectors {: 9d} to {: 12d} size {: 14d} Bytes{:s}".format(partNumber, name, startSector, endSector, byteLength, skippedText))


  def getPartitions(self, skippedPartitions : list = [], printResult : bool = True) -> bool:
    if not self.flashInfoGotten:
      if not self.getFlashInfo():
        return False
    
    partInfo = None
    try:
      partInfo = subprocess.Popen(['rkdeveloptool', 'list-partitions'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
      self.error("Unable to run 'rkdeveloptool list-partitions', is it in your $PATH?")
      return False
    stdout, stderr = partInfo.communicate()
    if partInfo.returncode != 0:
      self.error("FAILED: To have rkdeveloptool perform list-partitions, maybe it a different version\n")
      self.error(stdout.decode('utf-8'))
      return False
    result = stdout.decode('utf-8')
    lines = result.splitlines()
    match = re.search('#\s+LBA\s+start\s+\(sectors\)\s+LBA\s+end\s+\(sectors\)\s+Size\s+\(bytes\)\s+Name', lines[0])
    if not match:
      self.error("partition list header unknown, aborting")
      for line in lines:
        self.error(line)
      return False

    self.totalPartitionBytes = 0
    self.partitions = {}
    if printResult:
      print("Detected partitions:")
    for line in lines[1:]:
      match = re.search("(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\w+)$", line)
      if not match:
        self.error("Unable to parse line:")
        self.error(line)
        return False
      partNumber = int(match.group(1))
      startSector = int(match.group(2))
      endSector = int(match.group(3))
      byteLength = int(match.group(4))
      name = match.group(5)

      if partNumber == 0:
        self.addPartitionInformation(skippedPartitions, printResult, -1, 'data_at_beginning', 0, startSector-1, self.blockSize * (startSector-1))
      self.addPartitionInformation(skippedPartitions, printResult, partNumber, name, startSector, endSector, byteLength)
    return True

  def readFlashBlock(self, startSector : int, size : int, filename : str, dryRun : bool):
    if not dryRun:
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
    else:
      print("    Non dry run would have run 'rkdeveloptool read {:d} {:d} {:s}'".format(startSector, size, filename))

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
parser.add_argument('-d', '--destination', default="", type=str, help="The destination path to write the images to")
parser.add_argument('--skip-partition-table', action="store_true", help="Only for --type=partition, skip reading the bytes before the first partition")
parser.add_argument('-u', '--skip-userdata-partition', action="store_true", help="Skip the partition named 'userdata', it is large and Android should be able to recreate it")
parser.add_argument('-n', '--dry-run', action="store_true", help="Don't actually read bytes")
args = parser.parse_args()

readBlockSize = args.block_size
type = args.type
destination = args.destination
skippedPartitions = []
if args.skip_partition_table:
  skippedPartitions.append('data_at_beginning')
if args.skip_userdata_partition:
  skippedPartitions.append('userdata')
dryRun = args.dry_run

def handler(signum, frame):
  print("\nDetected Ctrl-C, your PineNote may become stuck and need to be powered off and placed in download mode again")
  print("Not all data have been downloaded")



signal.signal(signal.SIGINT, handler)

dut = RkDevelopTool()
if not dut.getFlashInfo():
  print("!!! An error was encounterd !!!")
  os._exit(1)
#Ensure the readBlockSize is in sectors sized blocks
readBlockSize = (int(readBlockSize/dut.blockSize)*dut.blockSize)
startTime = time.time()
bytesRead = 0



def readBlockOfData(startSector : int, endSector : int, filename: str, totalBytes : int) -> None:
  global dut
  global bytesRead
  global dryRun

  numberOfSectors : int = endSector-startSector+1
  byteSize : int = numberOfSectors * dut.blockSize
  localReadProgress : int = 0
  readCount :int = 0

  while localReadProgress < byteSize:
    if localReadProgress % dut.blockSize != 0:
      print("Internal error localReadProgress should have stayed in whole sectors")
      os._exit(1)
    progress = bytesRead * 100 / totalBytes
    etaString = "N.A."
    timePassed = time.time() - startTime
    if bytesRead != 0 and timePassed>0:
      bytesPerSecond = bytesRead/timePassed
      if bytesPerSecond > 0: 
        totalSeconds = totalBytes/bytesPerSecond
        secondsRemaining = int(totalSeconds - timePassed)
        if secondsRemaining < 0:
          secondsRemaining = 0
        etaString = secondsToString(secondsRemaining)

    outputName = filename
    readSize = byteSize - localReadProgress
    if readSize > readBlockSize:
      readSize = readBlockSize
    if (byteSize > readBlockSize):
      outputName = "{:s}.{:04d}".format(filename, readCount)

    sector = startSector + int(localReadProgress/dut.blockSize)
    print("Reading {: 12d} bytes from sector {: 9d} to {:15s} done: {:2.0f}% eta. {:s}".format(readSize, sector, outputName, progress, etaString))
    dut.readFlashBlock(sector, readSize, outputName, dryRun)
    readCount += 1
    localReadProgress += readSize
    bytesRead += readSize

if type=='disk':
  print()
  print()
  print("=== Beginning to read all flash data ===")
  name = "all_flash"
  if destination != "":
    name = destination+name
  readBlockOfData(0, dut.sectors-1, name, dut.sectors*dut.blockSize)

elif type=='partitions':
  if dut.getPartitions(skippedPartitions):
    print()
    print()
    print("=== Beginning reading data as partitions ===")
    for partitionNumber in dut.partitions:
      partData = dut.partitions[partitionNumber]
      if (partitionNumber >= 0):
        name = "{:02d}_{:s}".format(partitionNumber, partData['name'])
      else:
        name = partData['name']
      if destination != "":
        name = destination+name
      readBlockOfData(partData['startSector'], partData['endSector'], name, dut.totalPartitionBytes)
  else:
    print("!!! An error was encountered !!!")
    os._exit(1)