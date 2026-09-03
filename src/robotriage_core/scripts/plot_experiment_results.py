#!/usr/bin/env python3

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


INPUT_CSV = Path('results_decision_level/experiment_grid_summary.csv')
OUTPUT_DIR = Path('results_decision_level/plots')

NEW_METRIC_FIELDS = (
    'mean_task_success_rate_percent',
    'mean_decision_success_rate_percent',
    'plan_success_rate_percent',
    'mean_total_retries',
    'mean_total_attempts',
    'mean_total_duration_seconds',
    'reuse_decision_success_rate_percent',
    'remanufacture_decision_success_rate_percent',
    'recycle_decision_success_rate_percent',
)


def optional_float(row, field_name):
    value = row.get(field_name, '')
    if value == '':
        return None
    return float(value)


def read_results(csv_path):
    rows = []

    with csv_path.open('r', newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            result = {
                'success_probability': float(row['success_probability']),
                'max_retries': int(row['max_retries']),
                'mean_success_rate': float(row['mean_success_rate']),
                'mean_average_attempts': float(row['mean_average_attempts']),
                'mean_average_duration_seconds': float(
                    row['mean_average_duration_seconds']
                ),
                'status': row.get('status', ''),
            }
            for field_name in NEW_METRIC_FIELDS:
                result[field_name] = optional_float(row, field_name)
            rows.append(result)

    return rows


def completed_rows(rows):
    return [row for row in rows if row['status'] in ('', 'completed')]


def group_by(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    return grouped


def average(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


def save_plot(filename):
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=300)
    plt.close()


def plot_success_probability_vs_success_rate(rows):
    grouped = group_by(rows, 'max_retries')

    plt.figure()
    for max_retries in sorted(grouped):
        retry_rows = sorted(
            grouped[max_retries],
            key=lambda row: row['success_probability'],
        )
        x_values = [row['success_probability'] for row in retry_rows]
        y_values = [row['mean_success_rate'] for row in retry_rows]
        plt.plot(x_values, y_values, marker='o', label=f'max_retries={max_retries}')

    plt.title('Success Probability vs Success Rate')
    plt.xlabel('Configured success probability')
    plt.ylabel('Mean success rate (%)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    save_plot('success_probability_vs_success_rate.png')


def plot_retries_vs_success_rate(rows):
    grouped = group_by(rows, 'success_probability')

    plt.figure()
    for success_probability in sorted(grouped):
        probability_rows = sorted(
            grouped[success_probability],
            key=lambda row: row['max_retries'],
        )
        x_values = [row['max_retries'] for row in probability_rows]
        y_values = [row['mean_success_rate'] for row in probability_rows]
        plt.plot(
            x_values,
            y_values,
            marker='o',
            label=f'p={success_probability}',
        )

    plt.title('Max Retries vs Success Rate')
    plt.xlabel('Maximum retries')
    plt.ylabel('Mean success rate (%)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    save_plot('retries_vs_success_rate.png')


def plot_retries_vs_average_attempts(rows):
    grouped = group_by(rows, 'success_probability')

    plt.figure()
    for success_probability in sorted(grouped):
        probability_rows = sorted(
            grouped[success_probability],
            key=lambda row: row['max_retries'],
        )
        x_values = [row['max_retries'] for row in probability_rows]
        y_values = [row['mean_average_attempts'] for row in probability_rows]
        plt.plot(
            x_values,
            y_values,
            marker='o',
            label=f'p={success_probability}',
        )

    plt.title('Max Retries vs Average Attempts')
    plt.xlabel('Maximum retries')
    plt.ylabel('Mean average attempts')
    plt.legend()
    plt.grid(True, alpha=0.3)
    save_plot('retries_vs_average_attempts.png')


def plot_retries_vs_average_duration(rows):
    grouped = group_by(rows, 'success_probability')

    plt.figure()
    for success_probability in sorted(grouped):
        probability_rows = sorted(
            grouped[success_probability],
            key=lambda row: row['max_retries'],
        )
        x_values = [row['max_retries'] for row in probability_rows]
        y_values = [row['mean_average_duration_seconds'] for row in probability_rows]
        plt.plot(
            x_values,
            y_values,
            marker='o',
            label=f'p={success_probability}',
        )

    plt.title('Max Retries vs Average Duration')
    plt.xlabel('Maximum retries')
    plt.ylabel('Mean average duration (seconds)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    save_plot('retries_vs_average_duration.png')


def plot_metric_vs_retries(rows, metric, title, ylabel, filename):
    grouped = group_by(rows, 'success_probability')

    plt.figure()
    for success_probability in sorted(grouped):
        probability_rows = sorted(
            grouped[success_probability],
            key=lambda row: row['max_retries'],
        )
        available_rows = [
            row for row in probability_rows if row[metric] is not None
        ]
        if not available_rows:
            continue
        x_values = [row['max_retries'] for row in available_rows]
        y_values = [row[metric] for row in available_rows]
        plt.plot(
            x_values,
            y_values,
            marker='o',
            label=f'p={success_probability}',
        )

    plt.title(title)
    plt.xlabel('Maximum retries')
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True, alpha=0.3)
    save_plot(filename)


def plot_decision_type_success_rates(rows):
    representative_rows = sorted(
        [row for row in rows if row['success_probability'] == 0.5],
        key=lambda row: row['max_retries'],
    )

    plt.figure()
    for decision_type in ('reuse', 'remanufacture', 'recycle'):
        metric = f'{decision_type}_decision_success_rate_percent'
        available_rows = [
            row for row in representative_rows if row[metric] is not None
        ]
        if not available_rows:
            continue
        x_values = [row['max_retries'] for row in available_rows]
        y_values = [row[metric] for row in available_rows]
        plt.plot(x_values, y_values, marker='o', label=decision_type)

    plt.title('Decision-Type Success Rate vs Max Retries (p=0.5)')
    plt.xlabel('Maximum retries')
    plt.ylabel('Decision success rate (%)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    save_plot('decision_type_success_rate_vs_max_retries_p0_5.png')


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = completed_rows(read_results(INPUT_CSV))

    if not rows:
        raise RuntimeError('No completed experiment rows found to plot')

    plot_success_probability_vs_success_rate(rows)
    plot_retries_vs_success_rate(rows)
    plot_retries_vs_average_attempts(rows)
    plot_retries_vs_average_duration(rows)
    plot_metric_vs_retries(
        rows,
        'mean_decision_success_rate_percent',
        'Max Retries vs Decision Success Rate',
        'Mean decision success rate (%)',
        'max_retries_vs_decision_success_rate.png',
    )
    plot_metric_vs_retries(
        rows,
        'plan_success_rate_percent',
        'Max Retries vs Plan Success Rate',
        'Plan success rate (%)',
        'max_retries_vs_plan_success_rate.png',
    )
    plot_metric_vs_retries(
        rows,
        'mean_total_retries',
        'Max Retries vs Mean Total Retries',
        'Mean total retries',
        'max_retries_vs_mean_total_retries.png',
    )
    plot_decision_type_success_rates(rows)

    print(f'Plots saved to {OUTPUT_DIR}')


if __name__ == '__main__':
    main()