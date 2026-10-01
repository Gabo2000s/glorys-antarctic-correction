function fig = plot_ts(res, out_dir)
%PLOT_TS Temperature-salinity diagram of one station.
%   FIG = PLOT_TS(RES) draws the CTD (coloured by depth) and the corrected
%   GLORYS profile (black) in SA-Theta space, with sigma-0 isopycnals and the
%   boxes of Antarctic Surface Water (AASW), Winter Water (WW) and modified
%   Circumpolar Deep Water (mCDW).
%   PLOT_TS(RES, OUT_DIR) also saves TS_<label>.png in OUT_DIR.

ISOPYCNALS = 23:0.5:40;
GREY = [0.5 0.5 0.5];
deg_c = [char(176) 'C'];

fig = figure('Color', 'w', 'Position', [100 100 850 850]);
ax = axes(fig);
hold(ax, 'on');
box(ax, 'on');
set(ax, 'LineWidth', 1.5);
colormap(ax, flipud(jet(256)));

h_ctd = scatter(ax, res.SA_ctd, res.CT_ctd, 36, res.depth, 'o', 'filled');
h_cor = scatter(ax, res.SA_corrected, res.CT_corrected, 36, 'k', 'o', 'filled');

[SA, T, sigma0] = isopycnal_grid(res.SA_ctd, res.CT_ctd);
[c, h] = contour(ax, SA, T, sigma0, ISOPYCNALS, ':', 'Color', GREY);
clabel(c, h, 'LabelSpacing', 360, 'FontSize', 14, 'Color', GREY);
[SA, T, sigma0] = isopycnal_grid(res.SA_corrected, res.CT_corrected);
[c, h] = contour(ax, SA, T, sigma0, ':', 'Color', GREY);
clabel(c, h, 'LabelSpacing', 360, 'FontSize', 14, 'Color', GREY);

% Water masses: name, SA limits, Theta limits, colour, label position
masses = {
    'AASW', [33.0 34.29], [0.0 1.6], 'g', [33.6 1.2]
    'WW',   [33.4 34.4],  [-1.9 0.0], 'b', [34.2 -1.25]
    'mCDW', [34.3 35.0],  [0.0 1.6], 'r', [34.7 0.43]
};
for k = 1:size(masses, 1)
    sa = masses{k, 2};
    th = masses{k, 3};
    patch(ax, sa([1 2 2 1]), th([1 1 2 2]), masses{k, 4}, ...
          'FaceAlpha', 0.1, 'EdgeColor', masses{k, 4});
    text(ax, masses{k, 5}(1), masses{k, 5}(2), masses{k, 1}, ...
         'Color', masses{k, 4}, 'FontWeight', 'bold', 'FontSize', 14);
end

cb = colorbar(ax);
cb.Label.String = 'Depth (m)';
cb.Direction = 'reverse';
xlim(ax, [32.5 35]);
ylim(ax, [-1.6 1.6]);
xlabel(ax, 'SA (g kg^{-1})', 'FontSize', 14, 'FontWeight', 'bold');
ylabel(ax, ['Conservative Temperature (' deg_c ')'], 'FontSize', 14, 'FontWeight', 'bold');
title(ax, res.station.label, 'FontSize', 14);
set(ax, 'FontSize', 14);
axis(ax, 'square');
legend(ax, [h_ctd h_cor], {'CTD (colour = depth)', 'GLORYS corrected'}, ...
       'Location', 'southeast');

if nargin > 1 && ~isempty(out_dir)
    if ~exist(out_dir, 'dir'), mkdir(out_dir); end
    print(fig, fullfile(out_dir, ['TS_' res.station.label '.png']), '-dpng', '-r300');
end
end


function [SA, T, sigma0] = isopycnal_grid(sa, t)
% SA-Theta grid covering the profile and sigma-0 on it (reference 0 dbar).
SA_MIN = 22;
T_MIN = -2;
sa_max = max(sa, [], 'omitnan') + 0.1 * (max(sa, [], 'omitnan') - min(sa, [], 'omitnan'));
t_max = max(t, [], 'omitnan') + 0.1 * (max(t, [], 'omitnan') - min(t, [], 'omitnan'));
[SA, T] = meshgrid(SA_MIN:(sa_max - SA_MIN) / 600:sa_max, ...
                   T_MIN:(t_max - T_MIN) / 200:t_max);
sigma0 = gsw_rho(SA, T, 0) - 1000;
end
