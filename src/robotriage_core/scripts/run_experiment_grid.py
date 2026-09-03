#!/usr/bin/env python3

import argparse
import csv
import os
import signal
import subprocess
import time
from pathlib import Path


DEFAULT_SUCCESS_PROBABILITIES = [0.1, 0.3, 0.5, 0.7, 0.9]
DEFAULT_MAX_RETRIES_VALUES = [0, 1, 2, 4]
DEFAULT_MAX_TRIALS = 10
DEFAULT_OUTPUT_DIR = 'results'
DEFAULT_DOMAIN_START = 20


STATUS_COMPLETED = 'completed'
STATUS_MISSING_CSV = 'missing_csv'
STATUS_INCOMPLETE_TRIALS = 'incomplete_trials'


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Run a RoboTriage ROS2 experiment grid and summarise results.'
    )
    parser.add_argument(
        '--success-probabilities',
        nargs='+',
        type=float,
        default=DEFAULT_SUCCESS_PROBABILITIES,
        help='Success probability values to test. Default: 0.1 0.3 0.5 0.7 0.9',
    )
    parser.add_argument(
        '--max-retries-values',
        nargs='+',
        type=int,
        default=DEFAULT_MAX_RETRIES_VALUES,
        help='Maximum retry values to test. Default: 0 1 2 4',
    )
    parser.add_argument(
        '--max-trials',
        type=int,
        default=DEFAULT_MAX_TRIALS,
        help='Number of trials to record for each condition. Default: 10',
    )
    parser.add_argument(
        '--output-dir',
        default=DEFAULT_OUTPUT_DIR,
        help='Directory for experiment CSV outputs. Default: results',
    )
    parser.add_argument(
        '--summarise-only',
        action='store_true',
        help='Rebuild the summary CSV from existing per-condition CSV files without running ROS2 launches.',
    )
    parser.add_argument(
        '--domain-start',
        type=int,
        default=DEFAULT_DOMAIN_START,
        help='Starting ROS_DOMAIN_ID for experiment isolation. Default: 20',
    )
    return parser.parse_args()


def probability_label(success_probability):
    return str(success_probability).replace('.', '_')


def result_csv_path(results_dir, success_probability, max_retries):
    return results_dir / f'p{probability_label(success_probability)}_r{max_retries}.csv'


def count_trials(csv_path):
    if not csv_path.exists():
        return 0

    with csv_path.open('r', newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        return sum(1 for _ in reader)


def clean_fastdds_shared_memory():
    shm_dir = Path('/dev/shm')
    if not shm_dir.exists():
        return

    for path in shm_dir.glob('fastrtps_*'):
        try:
            path.unlink()
        except PermissionError:
            print(f'Warning: could not remove {path}; permission denied')
        except FileNotFoundError:
            pass


def stop_process(process):
    if process.poll() is not None:
        return

    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        process.wait()
    except ProcessLookupError:
        pass


def run_experiment(success_probability, max_retries, max_trials, output_csv, ros_domain_id):
    command = [
        'ros2',
        'launch',
        'robotriage_core',
        'robotriage_pipeline.launch.py',
        'enable_experiment_logger:=true',
        f'experiment_output_csv:={output_csv}',
        f'max_trials:={max_trials}',
        f'success_probability:={success_probability}',
        f'max_retries:={max_retries}',
    ]

    print(
        'Running experiment: '
        f'success_probability={success_probability}, '
        f'max_retries={max_retries}, '
        f'max_trials={max_trials}, '
        f'ROS_DOMAIN_ID={ros_domain_id}'
    )
    print(f'Waiting for {output_csv}')

    clean_fastdds_shared_memory()

    env = os.environ.copy()
    env['ROS_DOMAIN_ID'] = str(ros_domain_id)
    env['FASTDDS_BUILTIN_TRANSPORTS'] = env.get(
        'FASTDDS_BUILTIN_TRANSPORTS',
        'UDPv4',
    )

    process = subprocess.Popen(command, env=env, start_new_session=True)
    timeout_seconds = max_trials * 4 + 30
    start_time = time.time()
    last_reported_count = -1

    try:
        while time.time() - start_time < timeout_seconds:
            recorded_trials = count_trials(output_csv)

            if recorded_trials != last_reported_count:
                print(f'Collected {recorded_trials}/{max_trials} trials')
                last_reported_count = recorded_trials

            if output_csv.exists() and recorded_trials >= max_trials:
                print(f'Collected {max_trials}/{max_trials} trials in {output_csv}')
                return recorded_trials

            if process.poll() is not None:
                print('Launch process ended before all expected trials were collected')
                return recorded_trials

            time.sleep(1)

        recorded_trials = count_trials(output_csv)
        print(
            f'Timeout while waiting for {output_csv}; '
            f'collected {recorded_trials}/{max_trials} trials'
        )
        return recorded_trials

    finally:
        stop_process(process)
        time.sleep(1)


def mean(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


def read_float(row, field_name):
    value = row.get(field_name, '')
    if value == '':
        return 0.0
    return float(value)


def read_optional_float(row, field_name):
    value = row.get(field_name, '')
    if value == '':
        return None
    return float(value)


def mean_available(values):
    available_values = [value for value in values if value is not None]
    if not available_values:
        return ''
    return round(mean(available_values), 2)


def plan_success_rate(rows):
    values = []
    for row in rows:
        value = row.get('plan_success', '').strip().lower()
        if value in ('true', '1'):
            values.append(1.0)
        elif value in ('false', '0'):
            values.append(0.0)

    if not values:
        return ''
    return round(mean(values) * 100, 2)


def decision_type_success_rate(rows, decision_type):
    total_decisions = 0.0
    successful_decisions = 0.0
    found_values = False

    for row in rows:
        type_total = read_optional_float(
            row,
            f'{decision_type}_total_decisions',
        )
        type_successful = read_optional_float(
            row,
            f'{decision_type}_successful_decisions',
        )
        if type_total is None or type_successful is None:
            continue
        found_values = True
        total_decisions += type_total
        successful_decisions += type_successful

    if not found_values or total_decisions == 0:
        return ''
    return round(successful_decisions / total_decisions * 100, 2)


def missing_csv_summary(success_probability, max_retries, source_csv):
    print(
        'Warning: missing CSV for '
        f'success_probability={success_probability}, max_retries={max_retries}'
    )
    return {
        'success_probability': success_probability,
        'max_retries': max_retries,
        'mean_success_rate': 0,
        'mean_failed': 0,
        'mean_average_attempts': 0,
        'mean_average_duration_seconds': 0,
        'mean_task_success_rate_percent': '',
        'mean_decision_success_rate_percent': '',
        'plan_success_rate_percent': '',
        'mean_total_retries': '',
        'mean_total_attempts': '',
        'mean_total_duration_seconds': '',
        'reuse_decision_success_rate_percent': '',
        'remanufacture_decision_success_rate_percent': '',
        'recycle_decision_success_rate_percent': '',
        'number_of_trials': 0,
        'source_csv': str(source_csv),
        'status': STATUS_MISSING_CSV,
    }


def summarise_csv(success_probability, max_retries, source_csv, max_trials):
    if not source_csv.exists():
        return missing_csv_summary(success_probability, max_retries, source_csv)

    with source_csv.open('r', newline='', encoding='utf-8') as csv_file:
        rows = list(csv.DictReader(csv_file))

    status = STATUS_COMPLETED
    if len(rows) < max_trials:
        status = STATUS_INCOMPLETE_TRIALS
        print(
            'Warning: incomplete trials for '
            f'success_probability={success_probability}, max_retries={max_retries}; '
            f'collected {len(rows)}/{max_trials}'
        )

    return {
        'success_probability': success_probability,
        'max_retries': max_retries,
        'mean_success_rate': round(
            mean([read_float(row, 'success_rate') for row in rows]),
            2,
        ),
        'mean_failed': round(
            mean([read_float(row, 'failed') for row in rows]),
            2,
        ),
        'mean_average_attempts': round(
            mean([read_float(row, 'average_attempts') for row in rows]),
            2,
        ),
        'mean_average_duration_seconds': round(
            mean([read_float(row, 'average_duration_seconds') for row in rows]),
            2,
        ),
        'mean_task_success_rate_percent': mean_available([
            read_optional_float(row, 'task_success_rate_percent')
            for row in rows
        ]),
        'mean_decision_success_rate_percent': mean_available([
            read_optional_float(row, 'decision_success_rate_percent')
            for row in rows
        ]),
        'plan_success_rate_percent': plan_success_rate(rows),
        'mean_total_retries': mean_available([
            read_optional_float(row, 'total_retries') for row in rows
        ]),
        'mean_total_attempts': mean_available([
            read_optional_float(row, 'total_attempts') for row in rows
        ]),
        'mean_total_duration_seconds': mean_available([
            read_optional_float(row, 'total_duration_seconds')
            for row in rows
        ]),
        'reuse_decision_success_rate_percent': decision_type_success_rate(
            rows,
            'reuse',
        ),
        'remanufacture_decision_success_rate_percent': (
            decision_type_success_rate(rows, 'remanufacture')
        ),
        'recycle_decision_success_rate_percent': decision_type_success_rate(
            rows,
            'recycle',
        ),
        'number_of_trials': len(rows),
        'source_csv': str(source_csv),
        'status': status,
    }


def write_summary(summary_csv, summary_rows):
    fieldnames = [
        'success_probability',
        'max_retries',
        'mean_success_rate',
        'mean_failed',
        'mean_average_attempts',
        'mean_average_duration_seconds',
        'mean_task_success_rate_percent',
        'mean_decision_success_rate_percent',
        'plan_success_rate_percent',
        'mean_total_retries',
        'mean_total_attempts',
        'mean_total_duration_seconds',
        'reuse_decision_success_rate_percent',
        'remanufacture_decision_success_rate_percent',
        'recycle_decision_success_rate_percent',
        'number_of_trials',
        'source_csv',
        'status',
    ]

    with summary_csv.open('w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f'Wrote summary CSV: {summary_csv}')


def main():
    args = parse_arguments()
    results_dir = Path(args.output_dir)
    summary_csv = results_dir / 'experiment_grid_summary.csv'
    results_dir.mkdir(exist_ok=True)
    summary_rows = []

    condition_index = 0

    for success_probability in args.success_probabilities:
        for max_retries in args.max_retries_values:
            output_csv = result_csv_path(
                results_dir,
                success_probability,
                max_retries,
            )

            if not args.summarise_only:
                if output_csv.exists():
                    output_csv.unlink()

                ros_domain_id = args.domain_start + condition_index
                run_experiment(
                    success_probability,
                    max_retries,
                    args.max_trials,
                    output_csv,
                    ros_domain_id,
                )
            else:
                print(f'Summarising existing CSV: {output_csv}')

            summary_rows.append(
                summarise_csv(
                    success_probability,
                    max_retries,
                    output_csv,
                    args.max_trials,
                )
            )

            condition_index += 1

    write_summary(summary_csv, summary_rows)
    print('Experiment grid complete')


if __name__ == '__main__':
    main()