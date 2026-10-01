function res = correct_station(station, data_dir)
%CORRECT_STATION Adaptive thermodynamic correction of a GLORYS12V1 profile.
%   RES = CORRECT_STATION(STATION, DATA_DIR) corrects the GLORYS profile at
%   one CTD station. STATION is an element of STATION_LIST and DATA_DIR the
%   folder that contains ctd/ and glorys/.
%
%   The correction combines a depth-weighted bias term and a
%   stratification-weighted structural term, with an additional adjustment
%   where the Turner angle indicates diffusive convection. Step numbers in
%   the comments follow docs/method.md.
%
%   Temperatures are Conservative Temperature (Theta, degC) and salinities
%   Absolute Salinity (g/kg), the TEOS-10 variables. The CTD in-situ
%   temperature and the GLORYS potential temperature are both converted to
%   Theta, which is conserved when water masses mix and is the temperature
%   that the TEOS-10 functions used here (sigma0, alpha, beta) take. RES
%   contains, on the GLORYS levels:
%     depth, pressure                  level depth (m) and pressure (dbar)
%     SA_ctd, CT_ctd                   CTD profile
%     SA_raw, CT_raw                   GLORYS profile before correction
%     SA_corrected, CT_corrected       GLORYS profile after correction
%     bias_T, bias_S, N2, w_surface, w_structure, turner_angle,
%     diffusive_mask                   diagnostics
%   and station, latitude, longitude and metrics (bias, RMSE and Pearson
%   correlation, GLORYS minus CTD, before and after correction).

% Parameters
MIN_DEPTH = 0.5;              % step 2: shallower samples are discarded (m)
DZ = 1;                       % step 3: vertical bin size (m)
SGOLAY_CTD = 9;               % step 5: Savitzky-Golay window (bins)
MOVMEDIAN_BIAS = 7;           % step 11: moving-median window (levels)
MOVMEAN_GRAD = 7;             % step 13: moving-mean window (levels)
G = 9.81;                     % step 14: gravitational acceleration (m s-2)
RHO0 = 1027;                  % step 14: reference density (kg m-3)
L_SURFACE = 80;               % step 15: e-folding depth of the surface weight (m)
A_BIAS = 0.92;                % step 16: bias factor = A * w_surface + B
B_BIAS = 0.35;
KT = 4;                       % step 17: relaxation length for Theta (m)
KS = 2;                       % step 17: relaxation length for SA (m)
TU_LO = -90;                  % step 19: diffusive-convection range (deg)
TU_HI = -45;
F_DD = 0.08;                  % step 19: additional bias fraction
SGOLAY_FINAL = 7;             % step 20: Savitzky-Golay window (levels)
OUTLIER_WINDOW = 5;           % step 21: outlier window (levels)

% 1. Read the CTD cast ------------------------------------------------------
ctd = read_cnv(fullfile(data_dir, station.ctd_file));
depth_ctd = ctd.depSM(:);
t_ctd = ctd.tv290C(:);
sp_ctd = ctd.sal00(:);
lat = ctd.latitude;
lon = ctd.longitude;

% 2. Quality control: valid samples, below 0.5 m, downcast only -------------
keep = ~isnan(depth_ctd) & ~isnan(t_ctd) & ~isnan(sp_ctd);
depth_ctd = depth_ctd(keep);
t_ctd = t_ctd(keep);
sp_ctd = sp_ctd(keep);

keep = depth_ctd >= MIN_DEPTH;
depth_ctd = depth_ctd(keep);
t_ctd = t_ctd(keep);
sp_ctd = sp_ctd(keep);

keep = [true; diff(depth_ctd) > 0];
depth_ctd = depth_ctd(keep);
t_ctd = t_ctd(keep);
sp_ctd = sp_ctd(keep);

% 3. Median in 1 m bins -----------------------------------------------------
edges = 0:DZ:ceil(max(depth_ctd));
depth_bin = ((edges(1:end-1) + edges(2:end)) / 2)';
bins = discretize(depth_ctd, edges);
T_bin = accumarray(bins, t_ctd, [numel(depth_bin), 1], @median, NaN);
S_bin = accumarray(bins, sp_ctd, [numel(depth_bin), 1], @median, NaN);

% 4. Drop empty bins --------------------------------------------------------
keep = ~isnan(T_bin) & ~isnan(S_bin);
depth_bin = depth_bin(keep);
T_bin = T_bin(keep);
S_bin = S_bin(keep);

% 5. Savitzky-Golay smoothing -----------------------------------------------
T_bin = smoothdata(T_bin, 'sgolay', SGOLAY_CTD);
S_bin = smoothdata(S_bin, 'sgolay', SGOLAY_CTD);

% 6. TEOS-10 conversion of the CTD profile (in-situ temperature) ------------
p_bin = gsw_p_from_z(-depth_bin, lat);
SA_bin = gsw_SA_from_SP(S_bin, p_bin, lon, lat);
CT_bin = gsw_CT_from_t(SA_bin, T_bin, p_bin);
sigma0_bin = gsw_sigma0(SA_bin, CT_bin);

% 7. Read the GLORYS profile (median at each level) -------------------------
gl = readtable(fullfile(data_dir, station.glorys_file));
depth = gl.depth;
sp_raw = gl.salt_median;
theta_raw = gl.temp_median;

% 8. TEOS-10 conversion of the GLORYS profile (potential temperature) ------
pressure = gsw_p_from_z(-depth, lat);
SA_raw = gsw_SA_from_SP(sp_raw, pressure, lon, lat);
CT_raw = gsw_CT_from_pt(SA_raw, theta_raw);

% 9. CTD interpolated onto the GLORYS levels --------------------------------
CT_ctd = interp1(depth_bin, CT_bin, depth, 'makima', NaN);
SA_ctd = interp1(depth_bin, SA_bin, depth, 'makima', NaN);

% 10-11. Bias (GLORYS minus CTD), smoothed with a moving median -------------
bias_T = smoothdata(CT_raw - CT_ctd, 'movmedian', MOVMEDIAN_BIAS);
bias_S = smoothdata(SA_raw - SA_ctd, 'movmedian', MOVMEDIAN_BIAS);

% 12. Vertical gradients ----------------------------------------------------
dTdz_ctd = gradient(CT_ctd, depth);
dSdz_ctd = gradient(SA_ctd, depth);
dTdz_raw = gradient(CT_raw, depth);
dSdz_raw = gradient(SA_raw, depth);

% 13. Structural bias, smoothed with a moving mean --------------------------
grad_bias_T = smoothdata(dTdz_raw - dTdz_ctd, 'movmean', MOVMEAN_GRAD);
grad_bias_S = smoothdata(dSdz_raw - dSdz_ctd, 'movmean', MOVMEAN_GRAD);

% 14. Stratification N2 from the CTD (negative values set to zero) ----------
sigma0_ctd = interp1(depth_bin, sigma0_bin, depth, 'makima', NaN);
N2 = -(G / RHO0) .* gradient(sigma0_ctd, depth);
N2(N2 < 0) = 0;

% 15. Adaptive weights ------------------------------------------------------
w_surface = exp(-depth / L_SURFACE);
w_structure = N2 ./ max(N2, [], 'omitnan');
w_structure(isnan(w_structure)) = 0;

% 16. Bias term: factor 1.27 at the surface, tending to 0.35 at depth -------
bias_factor = A_BIAS .* w_surface + B_BIAS;
CT_corr = CT_raw - bias_factor .* bias_T;
SA_corr = SA_raw - bias_factor .* bias_S;

% 17. Structural term -------------------------------------------------------
kT = KT .* w_structure;
kS = KS .* w_structure;
CT_corr = CT_corr - kT .* grad_bias_T;
SA_corr = SA_corr - kS .* grad_bias_S;

% 18. Turner angle from the CTD ---------------------------------------------
alpha = gsw_alpha(SA_ctd, CT_ctd, pressure);
beta = gsw_beta(SA_ctd, CT_ctd, pressure);
turner = atan2d(alpha .* dTdz_ctd + beta .* dSdz_ctd, ...
                alpha .* dTdz_ctd - beta .* dSdz_ctd);

% 19. Additional adjustment in the diffusive-convection regime --------------
dd = turner > TU_LO & turner < TU_HI;
CT_corr(dd) = CT_corr(dd) - F_DD .* bias_T(dd);
SA_corr(dd) = SA_corr(dd) - F_DD .* bias_S(dd);

% 20. Final Savitzky-Golay smoothing ----------------------------------------
CT_corr = smoothdata(CT_corr, 'sgolay', SGOLAY_FINAL);
SA_corr = smoothdata(SA_corr, 'sgolay', SGOLAY_FINAL);

% 21. Outlier replacement; levels without GLORYS data set to missing ------
CT_corr = filloutliers(CT_corr, 'linear', 'movmedian', OUTLIER_WINDOW);
SA_corr = filloutliers(SA_corr, 'linear', 'movmedian', OUTLIER_WINDOW);
CT_corr(isnan(CT_raw)) = NaN;
SA_corr(isnan(SA_raw)) = NaN;

% 22. Metrics, GLORYS minus CTD, before and after correction ----------------
metrics.bias_T_before = mean(CT_raw - CT_ctd, 'omitnan');
metrics.bias_T_after = mean(CT_corr - CT_ctd, 'omitnan');
metrics.bias_S_before = mean(SA_raw - SA_ctd, 'omitnan');
metrics.bias_S_after = mean(SA_corr - SA_ctd, 'omitnan');
metrics.rmse_T_before = rms_difference(CT_raw, CT_ctd);
metrics.rmse_T_after = rms_difference(CT_corr, CT_ctd);
metrics.rmse_S_before = rms_difference(SA_raw, SA_ctd);
metrics.rmse_S_after = rms_difference(SA_corr, SA_ctd);
metrics.corr_T_before = pearson_r(CT_raw, CT_ctd);
metrics.corr_T_after = pearson_r(CT_corr, CT_ctd);
metrics.corr_S_before = pearson_r(SA_raw, SA_ctd);
metrics.corr_S_after = pearson_r(SA_corr, SA_ctd);

res = struct('station', station, 'latitude', lat, 'longitude', lon, ...
    'depth', depth, 'pressure', pressure, ...
    'SA_ctd', SA_ctd, 'CT_ctd', CT_ctd, 'SA_raw', SA_raw, 'CT_raw', CT_raw, ...
    'SA_corrected', SA_corr, 'CT_corrected', CT_corr, ...
    'bias_T', bias_T, 'bias_S', bias_S, 'N2', N2, ...
    'w_surface', w_surface, 'w_structure', w_structure, ...
    'turner_angle', turner, 'diffusive_mask', dd, 'metrics', metrics);
end


function value = rms_difference(a, b)
value = sqrt(mean((a - b).^2, 'omitnan'));
end


function r = pearson_r(a, b)
R = corrcoef(a, b, 'rows', 'complete');
r = R(1, 2);
end
