# A tool for backing up everything on a PineNote 

This tool needs a working rkdeveloptool, a patched u-boot and the PineNote needs to be in download mode

See [https://github.com/DorianRudolph/pinenotes](https://github.com/DorianRudolph/pinenotes) for instruction on getting those things.

The tool can both download the entire "disk" and the partitions as individual files.

Larger blocks of data will be split up to work around the 2GB limit in the current rkdeveloptool

For partitions the large and somewhat useless userdata partition can be skipped



## Usage

    usage: pinenote-backup.py [-h] [-b BLOCK_SIZE] -t {partitions,disk} [-d DESTINATION] [--skip-partition-table] [-u] [-n]
    
    A script for backing up a PineNote, may be useful for other devices using that can be accessed with rkdeveloptool
    
    options:
      -h, --help            show this help message and exit
      -b BLOCK_SIZE, --block_size BLOCK_SIZE
                            The max number of bytes to get at once, larger partitions/disks will be broken up into blocks according to this size to circumvent the 2GB limit, default is 1GB.
      -t {partitions,disk}, --type {partitions,disk}
                            The type of backup, partitions=attempt to get the individual partitions in separate files, disk=grap every byte including the partition table
      -d DESTINATION, --destination DESTINATION
                            The destination path to write the images to
      --skip-partition-table
                            Only for --type=partition, skip reading the bytes before the first partition
      -u, --skip-userdata-partition
                            Only for --type=partition, skip the partition named 'userdata', it is large and Android should be able to recreate it
      -n, --dry-run         Don't actually read bytes


## Example output 
    ./pinenote-backup.py -t partitions -u 
    Detected:
    Flash Size   : 512 MB
    Flash Sectors: 241827840
    Block Size   : 512 not kB
    Page Size    : 2 kB
    Detected partitions:
    -01 name: data_at_beginning  sectors         0 to        16383 size        8388096 Bytes
    000 name: uboot              sectors     16384 to        24575 size        4194304 Bytes
    001 name: trust              sectors     24576 to        32767 size        4194304 Bytes
    002 name: waveform           sectors     32768 to        36863 size        2097152 Bytes
    003 name: misc               sectors     36864 to        45055 size        4194304 Bytes
    004 name: dtbo               sectors     45056 to        53247 size        4194304 Bytes
    005 name: vbmeta             sectors     53248 to        55295 size        1048576 Bytes
    006 name: boot               sectors     55296 to       137215 size       41943040 Bytes
    007 name: security           sectors    137216 to       145407 size        4194304 Bytes
    008 name: recovery           sectors    145408 to       407551 size      134217728 Bytes
    009 name: backup             sectors    407552 to      1193983 size      402653184 Bytes
    010 name: cache              sectors   1193984 to      3291135 size     1073741824 Bytes
    011 name: metadata           sectors   3291136 to      3323903 size       16777216 Bytes
    012 name: super              sectors   3323904 to      9697279 size     3263168512 Bytes
    013 name: logo               sectors   9697280 to      9730047 size       16777216 Bytes
    014 name: device             sectors   9730048 to      9861119 size       67108864 Bytes
    015 name: userdata           sectors   9861120 to    241827775 size   118766927872 Bytes SKIPPED!
    
    
    === Beginning reading data as partitions ===
    Reading      8388608 bytes from sector         0 to data_at_beginning done:  0% eta. N.A.