
import logging
import os
import json

from helpers import *

class Experiment:
	def __init__(self, exp_id):
		assert len(exp_id.split('/')) == 4
		self.exp_id = exp_id
		self.exp_path = get_logs_path(exp_id)
		assert os.path.isdir(self.exp_path)

	def get_path(self, path, needfile = False):
		jpath = os.path.join(self.exp_path, path)
		if needfile and not os.path.isfile(jpath):
			raise Exception(f"file {jpath} doesn't exist")
		return jpath

	def get_exp_id(self):
		return self.exp_id

	def get_exp_arch(self):
		return os.path.basename(os.path.abspath(self.get_path("../../..")))

	def get_exp_type(self):
		return os.path.basename(os.path.abspath(self.get_path("../..")))

	def get_exp_params_id(self):
		return os.path.basename(os.path.abspath(self.get_path("..")))

	def get_prog_id(self):
		with open(self.get_path(f"code.hash", True), "r") as f:
			return f.read().strip()

	def get_code(self):
		prog_id = self.get_prog_id()
		with open(self.get_path(f"../../../progs/{prog_id}/code.asm", True), "r") as f:
			return f.read()

	def get_input_file(self, filename):
		with open(self.get_path(filename, True), "r") as f:
			return json.load(f)


	def is_valid_experiment(self):
		filespresent = True
		for filename in ["code.hash", "input1.json", "input2.json"]:
			filespresent = filespresent and os.path.isfile(self.get_path(filename))
		with open(self.get_path("code.hash", True), "r") as f:
			codehash = f.read().strip()
		filespresent = filespresent and os.path.isfile(self.get_path(f"../../../progs/{codehash}/code.asm"))
		return filespresent

	def is_incomplete_experiment(self, progplat_hash, board_type):
		is_complete = True
		# TODO: these filenames are specific to a certain type of experiment
		for filename in ["output_uart.log", "result.json"]:
			is_complete = is_complete and os.path.isfile(self.get_path(f"{progplat_hash}_{board_type}/{filename}"))
		return not is_complete

	def write_results(self, progplat_hash, board_type, outputs, force_results = False):
		exp_dir_results = self.get_path(f"{progplat_hash}_{board_type}")
		# create the directory
		call_cmd(["mkdir", "-p", exp_dir_results], "could not create directory")
		# write all data, one after the other and compare
		for (filename, bindata) in outputs:
			filepath = os.path.join(exp_dir_results, filename)
			writefile_or_compare(force_results, filepath, bindata, "files differ, check this")

	def print(self):
		assert self.get_exp_type() == "exps2"

		# read input files
		prog_id  = self.get_prog_id()
		code_asm = self.get_code()
		input1   = self.get_input_file("input1.json")
		input2   = self.get_input_file("input2.json")

		# printout
		print(f"prog_id = {prog_id}")
		print("="*20)
		print("="*20)
		print(code_asm)
		print("="*20)
		print("="*20)
		print(gen_readable(input1))
		print("="*20)
		print(gen_readable(input2))
		print("="*20)

