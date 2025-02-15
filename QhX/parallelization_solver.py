import sys
import time
from multiprocessing import Process
from multiprocessing import Queue
from QhX.detection import process1_new  # Fixed mode
from QhX.dynamical_mode import process1_new_dyn  # Dynamical mode
from QhX.iparallelization_solver import IParallelSolver
from QhX.utils.logger import Logger

DEFAULT_NTAU = None
DEFAULT_NGRID = None
DEFAULT_PROVIDED_MINFQ = None
DEFAULT_PROVIDED_MAXFQ = None
DEFAULT_LOG_PERIOD = 10.0  # Placeholder for log period
DEFAULT_NUM_WORKERS = 4  # Placeholder for the number of workers

# CSV format results header
HEADER = "ID,Sampling_1,Sampling_2,Common period (Band1 & Band2),Upper error bound,Lower error bound,Significance,Band1-Band2\n"

class ParallelSolver(IParallelSolver):
    """
    A class to manage parallel execution of data processing functions.
    """    
    def __init__(self,
                 delta_seconds=DEFAULT_LOG_PERIOD, 
                 num_workers=DEFAULT_NUM_WORKERS,
                 data_manager=None,
                 log_time=True, 
                 log_files=False,
                 save_results=True,
                 process_function=process1_new,  # Default is fixed mode
                 parallel_arithmetic=False,
                 ntau=DEFAULT_NTAU,
                 ngrid=DEFAULT_NGRID, 
                 provided_minfq=DEFAULT_PROVIDED_MINFQ, 
                 provided_maxfq=DEFAULT_PROVIDED_MAXFQ,
                 mode='fixed'  # New mode parameter, default to 'fixed'
                ):
        """Initialize the ParallelSolver with the specified configuration."""
        super().__init__(num_workers)
        self.delta_seconds = delta_seconds
        self.data_manager = data_manager
        self.save_results = save_results
        self.parallel_arithmetic = parallel_arithmetic
        self.ntau = ntau
        self.ngrid = ngrid
        self.provided_minfq = provided_minfq
        self.provided_maxfq = provided_maxfq
        self.mode = mode  # Set the mode
        self.logger = Logger(log_files, log_time, delta_seconds)

        # Determine the processing function based on the mode
        if self.mode == 'fixed':
            self.process_function = process1_new  # Use the fixed mode function
        elif self.mode == 'dynamical':
            self.process_function = process1_new_dyn  # Use the dynamical mode function
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def aggregate_process_function_result(self, result):
        """Places the result dict into a string"""
        res = ""
        for row in result:
            row_values = row.values() if isinstance(row, dict) else row
            res += ','.join([str(v) for v in row_values]) + "\n"
        return res

    def get_process_function_result(self, set_id):
        """Run the detection function and return the result"""
        result = self.process_function(self.data_manager,
                                       set_id, 
                                       ntau=self.ntau, 
                                       ngrid=self.ngrid, 
                                       provided_minfq=self.provided_minfq, 
                                       provided_maxfq=self.provided_maxfq, 
                                       parallel=self.parallel_arithmetic, 
                                       include_errors=False)
        return result
    
    def maybe_begin_logging(self, set_id):
        """Starts a logging thread"""
        self.logger.start(set_id)
    
    def maybe_stop_logging(self):
        """Stops the logger"""
        self.logger.stop()

    def maybe_save_local_results(self, set_id, res_string):
        """Saves local results of set ID formed into a string"""
        if self.save_results:
            with open(f'{set_id}-result.csv', 'w') as saving_file:
                saving_file.write(HEADER + res_string)

    def maybe_save_results(self, results_file):
        """If results file is set, saves the full results queue to it."""
        if results_file is not None:
            try:
                with open(results_file, 'w') as f:
                    f.write(HEADER)
                    while not self.results_.empty():
                        result = self.results_.get()
                        f.write(result)
            except Exception as e:
                print('Error while saving:', e)
