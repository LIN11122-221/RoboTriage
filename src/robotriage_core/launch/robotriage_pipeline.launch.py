from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    success_probability = LaunchConfiguration('success_probability')
    max_retries = LaunchConfiguration('max_retries')
    enable_experiment_logger = LaunchConfiguration('enable_experiment_logger')
    experiment_output_csv = LaunchConfiguration('experiment_output_csv')
    max_trials = LaunchConfiguration('max_trials')

    return LaunchDescription([
        DeclareLaunchArgument(
            'success_probability',
            default_value='0.85',
            description='Probability that each execution attempt succeeds',
        ),
        DeclareLaunchArgument(
            'max_retries',
            default_value='2',
            description='Maximum number of retries after a failed attempt',
        ),
        DeclareLaunchArgument(
            'enable_experiment_logger',
            default_value='false',
            description='Set to true to record evaluation summaries to CSV',
        ),
        DeclareLaunchArgument(
            'experiment_output_csv',
            default_value='experiment_results.csv',
            description='CSV file path for experiment results',
        ),
        DeclareLaunchArgument(
            'max_trials',
            default_value='10',
            description='Number of evaluation summaries to record',
        ),
        Node(
            package='robotriage_core',
            executable='decision_publisher_node',
            output='screen',
        ),
        Node(
            package='robotriage_core',
            executable='task_planner_node',
            output='screen',
        ),
        Node(
            package='robotriage_core',
            executable='execution_manager_node',
            output='screen',
            parameters=[{
                'success_probability': success_probability,
                'max_retries': max_retries,
            }],
        ),
        Node(
            package='robotriage_core',
            executable='evaluation_node',
            output='screen',
        ),
        Node(
            package='robotriage_core',
            executable='experiment_logger_node',
            output='screen',
            condition=IfCondition(enable_experiment_logger),
            parameters=[{
                'output_csv': experiment_output_csv,
                'max_trials': ParameterValue(max_trials, value_type=int),
            }],
        ),
    ])
