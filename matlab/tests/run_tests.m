function run_tests()
%RUN_TESTS Check the MATLAB implementation against the published results.
%   RUN_TESTS runs from any folder and checks that
%     1. read_cnv returns the expected channels and signed position;
%     2. the metrics reproduce the article's metrics table (printed with two
%        decimals, so within 0.006);
%     3. the metrics match results/metrics.csv (within 1e-6);
%     4. corrected profiles are missing exactly where GLORYS has no data;
%     5. the GLORYS temperature is read as potential temperature (converting
%        the raw Conservative Temperature back returns the file values).
%   It prints PASS/FAIL for each check and raises an error if any fails.
%   Requires the GSW Oceanographic Toolbox on the MATLAB path.

here = fileparts(mfilename('fullpath'));
matlab_dir = fileparts(here);
root = fileparts(matlab_dir);
addpath(matlab_dir);
data_dir = fullfile(root, 'data', 'raw');

names = {'bias_T_before', 'bias_T_after', 'bias_S_before', 'bias_S_after', ...
         'rmse_T_before', 'rmse_T_after', 'rmse_S_before', 'rmse_S_after', ...
         'corr_T_before', 'corr_T_after', 'corr_S_before', 'corr_S_after'};
% Table 2 of the revised article: levels without GLORYS data set to missing
% (step 21), and temperature computed as Conservative Temperature, with the
% GLORYS potential temperature converted by gsw_CT_from_pt.
article = [
    0.08  0.16 -0.80 0.14 0.53 0.28 1.18 0.21 0.82 0.97 0.92 0.91
    1.06  0.17 -0.45 0.16 1.21 0.55 0.85 0.22 0.77 0.83 0.88 0.94
    0.47  0.05 -0.76 0.16 0.72 0.34 1.11 0.25 0.78 0.89 0.84 0.84
    0.69 -0.05 -0.67 0.11 0.98 0.34 1.00 0.18 0.73 0.93 0.97 0.96
    0.79 -0.02 -0.39 0.14 1.30 0.55 0.77 0.20 0.43 0.67 0.91 0.96
    1.18  0.01 -0.46 0.12 1.45 0.45 0.75 0.18 0.63 0.81 0.94 0.96];
% Two printed decimals: up to 0.005 from rounding; four cells were rounded
% from three decimals (e.g. 1.1746 -> 1.175 -> 1.18), up to 0.0054.
ARTICLE_ATOL = 0.006;
RESULTS_ATOL = 1e-6;

failures = 0;

% 1. CTD reader
cast = read_cnv(fullfile(data_dir, 'ctd', 'NF003_008.cnv'));
ok = isequal(fieldnames(cast)', {'latitude', 'longitude', 'depSM', 'tv290C', ...
                                 'sal00', 'c0S_m', 'flag'}) ...
     && numel(cast.depSM) == 1482 ...
     && abs(cast.latitude + (68 + 9.73 / 60)) < 1e-12 ...
     && abs(cast.longitude + (69 + 32.12 / 60)) < 1e-12;
failures = failures + report('read_cnv: channels, length and position', ok, '');

% Metrics of the six stations
stations = station_list();
metrics = zeros(numel(stations), numel(names));
results = cell(1, numel(stations));
for k = 1:numel(stations)
    results{k} = correct_station(stations(k), data_dir);
    metrics(k, :) = cellfun(@(n) results{k}.metrics.(n), names);
end

% 2. Article table
d = max(abs(metrics(:) - article(:)));
failures = failures + report('metrics reproduce the article table', ...
    d <= ARTICLE_ATOL, sprintf('max difference %.4f', d));

% 3. Published results
published = readtable(fullfile(root, 'results', 'metrics.csv'));
expected = published{:, names};
d = max(abs(metrics(:) - expected(:)));
failures = failures + report('metrics match results/metrics.csv', ...
    d <= RESULTS_ATOL, sprintf('max difference %.2e', d));

% 4. Corrected profiles only where GLORYS has data
ok = all(cellfun(@(r) isequal(isnan(r.CT_corrected), isnan(r.CT_raw)) && ...
                      isequal(isnan(r.SA_corrected), isnan(r.SA_raw)), results));
failures = failures + report('corrected profiles missing where GLORYS is missing', ok, '');

% 5. GLORYS temperature read as potential temperature
d = 0;
for k = 1:numel(stations)
    gl = readtable(fullfile(data_dir, stations(k).glorys_file));
    r = results{k};
    d = max(d, max(abs(gsw_pt_from_CT(r.SA_raw, r.CT_raw) - gl.temp_median), [], 'omitnan'));
end
failures = failures + report('GLORYS temperature read as potential temperature', ...
    d <= 1e-10, sprintf('max difference %.1e', d));

if failures > 0
    error('run_tests:failed', '%d check(s) failed', failures);
end
fprintf('All checks passed.\n');
end


function failed = report(name, ok, detail)
if ok
    fprintf('PASS  %s  %s\n', name, detail);
    failed = 0;
else
    fprintf('FAIL  %s  %s\n', name, detail);
    failed = 1;
end
end
