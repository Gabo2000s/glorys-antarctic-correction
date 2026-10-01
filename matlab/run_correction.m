function results = run_correction(out_dir, make_figures)
%RUN_CORRECTION Correct the GLORYS12V1 profiles at the six stations.
%   RUN_CORRECTION corrects stations S1-S6 with data from data/raw, prints a
%   before -> after summary and writes outputs/matlab/:
%     metrics.csv                              metrics per station
%     summary.txt                              the printed summary
%     profiles/NF003_0XX_corrected_profile.csv profiles on the GLORYS levels
%   RUN_CORRECTION(OUT_DIR) writes to OUT_DIR instead.
%   RUN_CORRECTION(OUT_DIR, true) also writes figures/ (profiles and T-S).
%   RESULTS = RUN_CORRECTION(...) returns the CORRECT_STATION results.
%
%   Output formats are described in docs/outputs.md.

here = fileparts(mfilename('fullpath'));
root = fileparts(here);
data_dir = fullfile(root, 'data', 'raw');
if nargin < 1 || isempty(out_dir)
    out_dir = fullfile(root, 'outputs', 'matlab');
end
if nargin < 2
    make_figures = false;
end

stations = station_list();
results = cell(1, numel(stations));
for k = 1:numel(stations)
    results{k} = correct_station(stations(k), data_dir);
end
results = [results{:}];

for k = 1:numel(results)
    fprintf('%s\n', summary_block(results(k)));
end
write_outputs(results, out_dir);

if make_figures
    fig_dir = fullfile(out_dir, 'figures');
    for k = 1:numel(results)
        close(plot_profiles(results(k), fig_dir));
        close(plot_ts(results(k), fig_dir));
    end
end
fprintf('Outputs written to %s\n', out_dir);
end


function block = summary_block(res)
% Before -> after metrics of one station.
m = res.metrics;
st = res.station;
row = '  %-19s bias %7.3f -> %7.3f  RMSE %6.3f -> %6.3f  r %6.3f -> %6.3f\n';
block = [sprintf('%s  %s  %s\n', st.key, st.cast, st.label), ...
        sprintf(row, 'Temperature (degC)', m.bias_T_before, m.bias_T_after, ...
                m.rmse_T_before, m.rmse_T_after, m.corr_T_before, m.corr_T_after), ...
        sprintf(row, 'Salinity (g/kg)', m.bias_S_before, m.bias_S_after, ...
                m.rmse_S_before, m.rmse_S_after, m.corr_S_before, m.corr_S_after)];
end


function write_outputs(results, out_dir)
names = {'bias_T_before', 'bias_T_after', 'bias_S_before', 'bias_S_after', ...
         'rmse_T_before', 'rmse_T_after', 'rmse_S_before', 'rmse_S_after', ...
         'corr_T_before', 'corr_T_after', 'corr_S_before', 'corr_S_after'};
prof_dir = fullfile(out_dir, 'profiles');
if ~exist(prof_dir, 'dir'), mkdir(prof_dir); end

% metrics.csv
fid = fopen(fullfile(out_dir, 'metrics.csv'), 'w');
fprintf(fid, 'station,%s\n', strjoin(names, ','));
for k = 1:numel(results)
    values = cellfun(@(n) results(k).metrics.(n), names);
    fprintf(fid, '%s', results(k).station.key);
    fprintf(fid, ',%.15g', values);
    fprintf(fid, '\n');
end
fclose(fid);

% summary.txt
fid = fopen(fullfile(out_dir, 'summary.txt'), 'w');
for k = 1:numel(results)
    if k > 1, fprintf(fid, '\n'); end
    fprintf(fid, '%s', summary_block(results(k)));
end
fclose(fid);

% profiles
header = ['depth_m,pressure_dbar,SA_ctd_gkg,CT_ctd_degC,SA_glorys_raw_gkg,' ...
          'CT_glorys_raw_degC,SA_glorys_corrected_gkg,CT_glorys_corrected_degC,' ...
          'N2_s-2,turner_angle_deg,w_surface,w_structure,diffusive_convection'];
for k = 1:numel(results)
    r = results(k);
    cols = [r.depth, r.pressure, r.SA_ctd, r.CT_ctd, r.SA_raw, r.CT_raw, ...
            r.SA_corrected, r.CT_corrected, r.N2, r.turner_angle, ...
            r.w_surface, r.w_structure];
    file = fullfile(prof_dir, [r.station.cast '_corrected_profile.csv']);
    fid = fopen(file, 'w');
    fprintf(fid, '%s\n', header);
    for i = 1:size(cols, 1)
        fprintf(fid, '%.6f,', cols(i, :));
        fprintf(fid, '%d\n', r.diffusive_mask(i));
    end
    fclose(fid);
end
end
