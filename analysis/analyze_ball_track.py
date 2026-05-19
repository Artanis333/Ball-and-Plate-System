import argparse
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


PX_TO_MM = 400.0 / 256.0


def parse_args():
    parser = argparse.ArgumentParser(description='Analyze MAIXCAM ball trajectory data.')
    parser.add_argument('csv_path', nargs='?', default='ball_track_1777283591903.csv',
                        help='CSV file with ball trajectory data')
    parser.add_argument('--start-time', type=float, default=None,
                        help='Start time in seconds relative to the first timestamp for segment analysis')
    parser.add_argument('--end-time', type=float, default=None,
                        help='End time in seconds relative to the first timestamp for segment analysis')
    parser.add_argument('--start-index', type=int, default=None,
                        help='Start row index for segment analysis (0-based, detected points only)')
    parser.add_argument('--end-index', type=int, default=None,
                        help='End row index for segment analysis (inclusive, detected points only)')
    parser.add_argument('--show-full-trajectory', action='store_true',
                        help='Draw the full trajectory in the trajectory plot and highlight the selected segment')
    parser.add_argument('--smooth-window', type=int, default=7,
                        help='Rolling window size for smoothing curves (>=1)')
    parser.add_argument('--vel-avg-window', type=int, default=5,
                        help='Rolling-average window for velocity after low-pass filter (>=1)')
    return parser.parse_args()


def load_data(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f'File not found: {csv_path}')

    df = pd.read_csv(csv_path)
    found_df = df[df['found'] == 1].copy()
    if found_df.empty:
        raise ValueError('No detected ball records found in data.')

    found_df['time_s'] = (found_df['timestamp_ms'] - found_df['timestamp_ms'].iloc[0]) / 1000.0
    return df, found_df


def select_segment(found_df: pd.DataFrame,
                   start_time: float = None,
                   end_time: float = None,
                   start_index: int = None,
                   end_index: int = None) -> pd.DataFrame:
    segment = found_df

    if start_time is not None or end_time is not None:
        if start_time is None:
            start_time = 0.0
        if end_time is None:
            end_time = segment['time_s'].iloc[-1]
        segment = segment[(segment['time_s'] >= start_time) & (segment['time_s'] <= end_time)].copy()

    if start_index is not None or end_index is not None:
        if start_index is None:
            start_index = 0
        if end_index is None:
            end_index = len(segment) - 1
        segment = segment.iloc[start_index:end_index + 1].copy()

    if segment.empty:
        raise ValueError('Selected segment is empty. Please adjust start/end time or index.')

    return segment


def compute_speed(segment: pd.DataFrame) -> pd.DataFrame:
    segment['dx'] = segment['x'].diff()
    segment['dy'] = segment['y'].diff()
    segment['dt_s'] = segment['time_s'].diff()
    # 带符号相对速度（相邻采样点差分）
    segment['vx'] = segment['dx'] / segment['dt_s']
    segment['vy'] = segment['dy'] / segment['dt_s']
    return segment


def lowpass_filter_series(series: pd.Series, window: int) -> pd.Series:
    if window <= 1:
        return series
    alpha = 2.0 / (window + 1.0)
    filtered = []
    prev = None
    for val in series:
        if pd.isna(val):
            filtered.append(prev if prev is not None else val)
            continue
        if prev is None or pd.isna(prev):
            prev = val
        else:
            prev = alpha * val + (1.0 - alpha) * prev
        filtered.append(prev)
    return pd.Series(filtered, index=series.index)


def rolling_average_series(series: pd.Series, window: int) -> pd.Series:
    if window <= 1:
        return series
    return series.rolling(window=window, center=True, min_periods=1).mean()


def beautify_plot_style():
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Noto Sans CJK SC', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False


def save_plots(found_df: pd.DataFrame,
               segment: pd.DataFrame,
               output_prefix: str,
               show_full_trajectory: bool,
               smooth_window: int,
               vel_avg_window: int):
    beautify_plot_style()

    found_plot = found_df.copy()
    segment_plot = segment.copy()

    # 单位换算：pixel -> mm
    for df_plot in [found_plot, segment_plot]:
        df_plot['x_mm'] = df_plot['x'] * PX_TO_MM
        df_plot['y_mm'] = df_plot['y'] * PX_TO_MM

    # 低通滤波
    found_plot['x_mm_f'] = lowpass_filter_series(found_plot['x_mm'], smooth_window)
    found_plot['y_mm_f'] = lowpass_filter_series(found_plot['y_mm'], smooth_window)
    segment_plot['x_mm_f'] = lowpass_filter_series(segment_plot['x_mm'], smooth_window)
    segment_plot['y_mm_f'] = lowpass_filter_series(segment_plot['y_mm'], smooth_window)
    segment_plot['vx_mm_s'] = segment_plot['vx'] * PX_TO_MM
    segment_plot['vy_mm_s'] = segment_plot['vy'] * PX_TO_MM
    segment_plot['vx_mm_s_f'] = lowpass_filter_series(segment_plot['vx_mm_s'], smooth_window)
    segment_plot['vy_mm_s_f'] = lowpass_filter_series(segment_plot['vy_mm_s'], smooth_window)
    # 二级去噪：低通滤波后再滚动平均
    segment_plot['vx_mm_s_ff'] = rolling_average_series(segment_plot['vx_mm_s_f'], vel_avg_window)
    segment_plot['vy_mm_s_ff'] = rolling_average_series(segment_plot['vy_mm_s_f'], vel_avg_window)

    # 轨迹图
    plt.figure(figsize=(8.5, 8))
    if show_full_trajectory:
        plt.plot(found_plot['x_mm_f'], found_plot['y_mm_f'], color='#A0A0A0', linewidth=1.2, alpha=0.55, label='全时段轨迹')
    plt.plot(segment_plot['x_mm_f'], segment_plot['y_mm_f'], linewidth=2.2, color='#1f77b4', label='切分段轨迹')
    plt.scatter(segment_plot['x_mm_f'].iloc[0], segment_plot['y_mm_f'].iloc[0], color='#2ca02c', s=75, label='起点')
    plt.scatter(segment_plot['x_mm_f'].iloc[-1], segment_plot['y_mm_f'].iloc[-1], color='#d62728', s=75, label='终点')
    plt.gca().invert_yaxis()
    plt.xlabel('X 位置 (mm)', fontsize=11)
    plt.ylabel('Y 位置 (mm)', fontsize=11)
    plt.legend()
    plt.grid(True)
    plt.savefig(Path(f'{output_prefix}_trajectory.png'), dpi=150, bbox_inches='tight')
    plt.close()

    # 速度图
    speed_df = segment_plot.dropna(subset=['vx_mm_s_ff', 'vy_mm_s_ff']).copy()
    plt.figure(figsize=(10, 5))
    plt.plot(speed_df['time_s'], speed_df['vx_mm_s_ff'], linewidth=1.9, color='#ff7f0e', label='相对速度 X')
    plt.plot(speed_df['time_s'], speed_df['vy_mm_s_ff'], linewidth=1.9, color='#9467bd', label='相对速度 Y')
    plt.axhline(0, color='#777777', linewidth=1.0, linestyle='--')
    plt.xlabel('时间 (s)', fontsize=11)
    plt.ylabel('速度 (mm/s)', fontsize=11)
    plt.legend()
    plt.grid(True)
    plt.savefig(Path(f'{output_prefix}_speed.png'), dpi=150, bbox_inches='tight')
    plt.close()

    # 位置随时间图
    plt.figure(figsize=(10, 6))
    plt.plot(segment_plot['time_s'], segment_plot['x_mm_f'], label='X 方向', linewidth=2.0, color='#1f77b4')
    plt.plot(segment_plot['time_s'], segment_plot['y_mm_f'], label='Y 方向', linewidth=2.0, color='#2ca02c')
    plt.xlabel('时间 (s)', fontsize=11)
    plt.ylabel('位置 (mm)', fontsize=11)
    plt.legend()
    plt.grid(True)
    plt.savefig(Path(f'{output_prefix}_position_time.png'), dpi=150, bbox_inches='tight')
    plt.close()


def save_summary(df: pd.DataFrame, segment: pd.DataFrame, output_prefix: str):
    vel_df = segment.dropna(subset=['vx', 'vy']).copy()
    vx_mm_s = vel_df['vx'] * PX_TO_MM
    vy_mm_s = vel_df['vy'] * PX_TO_MM
    segment_x_mm = segment['x'] * PX_TO_MM
    segment_y_mm = segment['y'] * PX_TO_MM

    stats = {
        'total_records': len(df),
        'detected_records': len(df[df['found'] == 1]),
        'segment_records': len(segment),
        'segment_start_time_s': float(segment['time_s'].iloc[0]),
        'segment_end_time_s': float(segment['time_s'].iloc[-1]),
        'segment_duration_s': float(segment['time_s'].iloc[-1] - segment['time_s'].iloc[0]),
        'x_min_mm': float(segment_x_mm.min()),
        'x_max_mm': float(segment_x_mm.max()),
        'y_min_mm': float(segment_y_mm.min()),
        'y_max_mm': float(segment_y_mm.max()),
        'mean_vx_mm_s': float(vx_mm_s.mean()),
        'mean_vy_mm_s': float(vy_mm_s.mean()),
        'max_vx_mm_s': float(vx_mm_s.max()),
        'min_vx_mm_s': float(vx_mm_s.min()),
        'max_vy_mm_s': float(vy_mm_s.max()),
        'min_vy_mm_s': float(vy_mm_s.min()),
    }

    report_path = Path(f'{output_prefix}_analysis_summary.txt')
    with report_path.open('w') as f:
        for key, value in stats.items():
            f.write(f'{key}: {value}\n')

    return report_path


if __name__ == '__main__':
    args = parse_args()
    csv_path = Path(args.csv_path)

    df, found_df = load_data(csv_path)
    segment = select_segment(found_df,
                             start_time=args.start_time,
                             end_time=args.end_time,
                             start_index=args.start_index,
                             end_index=args.end_index)
    segment = compute_speed(segment)

    output_prefix = csv_path.stem
    if args.start_time is not None or args.end_time is not None:
        output_prefix += f'_t{args.start_time or 0:.2f}-{args.end_time or segment["time_s"].iloc[-1]:.2f}'
    if args.start_index is not None or args.end_index is not None:
        output_prefix += f'_i{args.start_index or 0}-{args.end_index if args.end_index is not None else len(segment)-1}'

    save_plots(
        found_df,
        segment,
        output_prefix,
        args.show_full_trajectory,
        args.smooth_window,
        args.vel_avg_window,
    )
    report_path = save_summary(df, segment, output_prefix)

    print('Analysis completed.')
    print(f'Trajectory saved to {output_prefix}_trajectory.png')
    print(f'Speed plot saved to {output_prefix}_speed.png')
    print(f'Position-time plot saved to {output_prefix}_position_time.png')
    print(f'Summary saved to {report_path}')
