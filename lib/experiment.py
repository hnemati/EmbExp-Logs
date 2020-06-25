
import logging
import os
import json
import shutil


from helpers import *

def get_run_id(progplat_hash, board_type):
	return f"{progplat_hash}.{board_type}"
def get_run_dir(run_id):
	return f"run.{run_id}"

class Experiment:
	def __init__(self, exp_id):
		assert len(exp_id.split('/')) == 4
		self.exp_id = exp_id
		self.exp_path = get_logs_path(exp_id)
		assert os.path.isdir(self.exp_path)
		self.tries = 0
		self.last_run_id = None

	def create(exp_id, files):
		exp_path = get_logs_path(exp_id)
		# create experiment directory, exception if it already exists
		exp_dir_path = os.path.dirname(exp_path)
		if not os.path.isdir(exp_dir_path):
			os.makedirs(exp_dir_path)
		os.mkdir(exp_path)
		# write all data, one after the other
		for (filename, bindata) in files:
			filepath = os.path.join(exp_path, filename)
			writefile_or_compare(False, filepath, bindata, "this should never happen")
		return Experiment(exp_id)

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

	def get_exp_data_id(self):
		return os.path.basename(os.path.abspath(self.get_path(".")))

	def get_prog_id(self):
		with open(self.get_path(f"code.hash", True), "r") as f:
			return f.read().strip()

	def get_prog_path(self, path, needfile = False):
		prog_id = self.get_prog_id()
		return self.get_path(f"../../../progs/{prog_id}/{path}", needfile)

	def get_code(self):
		with open(self.get_prog_path("code.asm", True), "r") as f:
			return f.read()

	def get_input_file(self, filename):
		with open(self.get_path(filename, True), "r") as f:
			return json.load(f)

	def get_result_file(self, run_id, filename):
		filepath = f"{get_run_dir(run_id)}/{filename}"
		with open(self.get_path(filepath, True), "r") as f:
			return json.load(f)

	def remove_run(self, run_id):
		directory = get_run_dir(run_id)
		if not os.path.isdir(directory):
		#try:
		shutil.rmtree(directory)
		#except OSError as e:
		#	print("Error: %s : %s" % (run_res_dir, e.strerror))

	def get_exp_gens(self):
		prefix = "gen."
		gens = []
		for f in os.listdir(self.get_path(".")):
			if os.path.isfile(self.get_path(f)) and f.startswith(prefix):
				gens.append(f)
		return gens

	def get_prog_gens(self):
		prefix = "gen."
		gens = []
		for f in os.listdir(self.get_prog_path(".")):
			if os.path.isfile(self.get_prog_path(f)) and f.startswith(prefix):
				gens.append(f)
		return gens

	def get_run_ids(self):
		prefix = "run."
		ids = []
		for d in os.listdir(self.get_path(".")):
			if os.path.isdir(self.get_path(d)) and d.startswith(prefix):
				ids.append(d[len(prefix):])
		return ids

	def is_valid_experiment(self):
		filenames = ["code.hash", "input1.json"] + (["input2.json"] if self.get_exp_type() == "exps2" else [])
		for filename in filenames:
			if not os.path.isfile(self.get_path(filename)):
				return False
			if filename.endswith(".json"):
				with open(self.get_path(filename, True), "r") as f:
					try:
						if not isinstance(json.load(f), dict):
							return False
					except:
						return False
		if not os.path.isfile(self.get_prog_path("code.asm")):
			return False
		return True

	def is_incomplete_experiment(self, run_id):
		is_complete = True
		# TODO: these filenames are specific to a certain type of experiment
		for filename in ["output_uart.log", "result.json"]:
			is_complete = is_complete and os.path.isfile(self.get_path(f"{get_run_dir(run_id)}/{filename}"))
		# if experiment was complete and resulted in exception, try it up to 3 times
		assert self.last_run_id != None
		if is_complete:
			run_id      = self.last_run_id
			content     = self.get_result_file(run_id, "result.json")
			is_exception = "exception" in str(content)

			if is_exception:
				self.tries += 1
				self.remove_run(run_id)
			is_complete = is_complete and (not (is_exception and (self.tries < 3))) 	
		
		return not is_complete

	def write_results(self, run_id, outputs, force_results = False):
		exp_dir_results = self.get_path(get_run_dir(run_id))
		# create the directory
		call_cmd(["mkdir", "-p", exp_dir_results], "could not create directory")
		nomismatches = True
		# find whether there are mismatches
		for (filename, bindata) in outputs:
			filepath = os.path.join(exp_dir_results, filename)
			nomismatches = nomismatches and comparefile(filepath, bindata)
		if not force_results and not nomismatches:
			return False
		# write all data, one after the other
		for (filename, bindata) in outputs:
			filepath = os.path.join(exp_dir_results, filename)
			writefile_or_compare(force_results, filepath, bindata, "this should never happen")
		return nomismatches

	def print(self):
		print("generation info:")
		print("-"*40)
		for g in self.get_exp_gens():
			print(f"- {g}")
		print()

		print("runs:")
		print("-"*40)
		for g in self.get_run_ids():
			print(f"- {g}")
		print()

		print("configuration:")
		print("-"*40)
		assert self.get_exp_type() == "exps2" or self.get_exp_type() == "exps1"

		# read input files
		prog_id  = self.get_prog_id()
		code_asm = self.get_code()
		input1   = self.get_input_file("input1.json")
		if self.get_exp_type() == "exps2":
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
		if self.get_exp_type() == "exps2":
			print(gen_readable(input2))
			print("="*20)

		print("prog generation info:")
		print("-"*40)
		for g in self.get_prog_gens():
			print(f"- {g}")
		print()

