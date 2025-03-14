import logging
import os
import math
from pathlib import Path
from typing import Literal

import numpy as np

from concurrent.futures import ProcessPoolExecutor

from layup.utilities.file_io.CSVReader import CSVDataReader
from layup.utilities.file_io.HDF5Reader import HDF5DataReader
from layup.utilities.file_io.file_output import write_csv, write_hdf5

logger = logging.getLogger(__name__)


def process_data(data, n_workers, func, **kwargs):
    """
    Process a structured numpy array in parallel for a given function and keyword arguments

    Parameters
    ----------
    data : numpy structured array
        The data to process.
    n_workers : int
        The number of workers to use for parallel processing.
    func : function
        The function to apply to each block of data within parallel.
    **kwargs : dictionary
        Extra arguments to pass to the function.

    Returns
    -------
    res : numpy structured array
        The processed data concatenated from each function result
    """
    # Divide our data into blocks to be processed by each worker
    block_size = max(1, int(len(data) / n_workers))
    # Create a list of tuples of the form (start, end) where start is the starting index of the block
    # and end is the last index of the block + 1.
    blocks = [(i, min(i + block_size, len(data))) for i in range(0, len(data), block_size)]

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        # Create a future applying the function to each block of data
        futures = [executor.submit(func, data[start:end], **kwargs) for start, end in blocks]
        # Concatenate all processed blocks together as our final result
        return np.concatenate([future.result() for future in futures])


def _apply_convert(data, convert_to):
    """
    Apply the appropiate conversion function to the data

    Parameters
    ----------
    data : numpy structured array
        The data to convert.
    convert_to : str
        The orbital format to convert the data to. Must be one of: "BCART", "BCOM", "BKEP", "CART", "COM", "KEP"

    Returns
    -------
    data : numpy structured array
        The converted data
    """
    # TODO(wbeebe): Implement actual conversion logic
    return data


def convert(data, convert_to, num_workers=1):
    """
    Convert a structured numpy array to a different orbital format with support for parallel processing

    Parameters
    ----------
    data : numpy structured array
        The data to convert.
    convert_to : str
        The format to convert the data to. Must be one of: "BCART", "BCOM", "BKEP", "CART", "COM", "KEP"
    num_workers : int, optional (default=1)
        The number of workers to use for parallel processing.

    Returns
    -------
    data : numpy structured array
        The converted data
    """
    if num_workers == 1:
        return _apply_convert(data, convert_to)
    # Parallelize the conversion of the data across the requested number of workers
    return process_data(data, num_workers, _apply_convert, convert_to=convert_to)


def convert_cli(
    input: str,
    output_file_stem: str,
    convert_to: Literal["BCART", "BCOM", "BKEP", "CART", "COM", "KEP"],
    file_format: Literal["csv", "hdf5"] = "csv",
    chunk_size: int = 10_000,
    num_workers: int = -1,
):
    """
    Convert an orbit file from one format to another with support for parallel processing.

    Note that the output file will be written in the caller's current working directory.

    Parameters
    ----------
    input : str
        The path to the input file.
    output_file_stem : str
        The stem of the output file.
    convert_to : str
        The format to convert the input file to. Must be one of: "BCART", "BCOM", "BKEP", "CART", "COM", "KEP"
    file_format : str, optional (default="csv")
        The format of the output file. Must be one of: "csv", "hdf5"
    chunk_size : int, optional (default=10_000)
        The number of rows to read in at a time.
    num_workers : int, optional (default=-1)
        The number of workers to use for parallel processing. If -1, the number of workers will be set to the number of CPUs on the system.
    """
    input_file = Path(input)
    if file_format == "csv":
        output_file = Path(f"{output_file_stem}.{file_format.lower()}")
    else:
        output_file = Path(f"{output_file_stem}")
    output_directory = output_file.parent.resolve()

    if num_workers < 0:
        num_workers = os.cpu_count()

    # Check that input file exists
    if not input_file.exists():
        logger.error(f"Input file {input_file} does not exist")

    # Check that output directory exists
    if not output_directory.exists():
        logger.error(f"Output directory {output_directory} does not exist")

    # Check that chunk size is a positive integer
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        logger.error("Chunk size must be a positive integer")

    # Check that the file format is valid
    if file_format.lower() not in ["csv", "hdf5"]:
        logger.error("File format must be 'csv' or 'hdf5'")

    # Check that the conversion type is valid
    if convert_to not in ["BCART", "BCOM", "BKEP", "CART", "COM", "KEP"]:
        logger.error("Conversion type must be 'BCART', 'BCOM', 'BKEP', 'CART', 'COM', or 'KEP'")

    # Open the input file and read the first line
    if file_format is "hdf5":
        reader = HDF5DataReader(input_file, format_column_name="FORMAT")
    else:
        reader = CSVDataReader(input_file, format_column_name="FORMAT")

    sample_data = reader.read_rows(block_start=0, block_size=1)

    # Check orbit format in the file
    input_format = None
    if "FORMAT" in sample_data.dtype.names:
        input_format = sample_data["FORMAT"][0]
        if input_format not in ["BCART", "BCOM", "BKEP", "CART", "COM", "KEP"]:
            logger.error(f"Input file contains invalid 'FORMAT' column: {input_format}")
    else:
        logger.error("Input file does not contain 'FORMAT' column")

    # Check that the input format is not already the desired format
    if convert_to == input_format:
        logger.error("Input file is already in the desired format")

    # Calculate the start and end indices for each chunk, as a list of tuples
    # of the form (start, end) where start is the starting index of the chunk
    # and the last index of the chunk + 1.
    total_rows = reader.get_row_count()
    chunks = [(i, min(i + chunk_size, total_rows)) for i in range(0, total_rows, chunk_size)]

    for chunk_start, chunk_end in chunks:
        # Read the chunk of data
        chunk_data = reader.read_rows(block_start=chunk_start, block_size=chunk_end - chunk_start)
        # Parallelize conversion of this chunk of data.
        converted_data = convert(chunk_data, convert_to, num_workers=num_workers)
        # Write out the converted data in in the requested file format.
        if file_format == "hdf5":
            write_hdf5(converted_data, output_file, key="data")
        else:
            write_csv(converted_data, output_file)

    print(f"Data has been written to {output_file}")
