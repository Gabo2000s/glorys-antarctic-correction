function fig = plot_profiles(res, out_dir)
%PLOT_PROFILES Absolute Salinity and Conservative Temperature against depth.
%   FIG = PLOT_PROFILES(RES) draws the CTD, raw GLORYS and corrected GLORYS
%   profiles of one station (RES from CORRECT_STATION).
%   PLOT_PROFILES(RES, OUT_DIR) also saves profiles_<label>.png in OUT_DIR.

st = res.station;
deg_c = [char(176) 'C'];
fig = figure('Color', 'w', 'Position', [100 100 1100 600]);
panels = {
    res.SA_ctd, res.SA_raw, res.SA_corrected, 'Absolute Salinity (g kg^{-1})', 'Salinity'
    res.CT_ctd, res.CT_raw, res.CT_corrected, ['Conservative Temperature (' deg_c ')'], 'Temperature'
};
for k = 1:2
    ax = subplot(1, 2, k);
    hold(ax, 'on');
    plot(ax, panels{k, 1}, -res.depth, 'k', 'LineWidth', 2);
    plot(ax, panels{k, 2}, -res.depth, '--r', 'LineWidth', 1.5);
    plot(ax, panels{k, 3}, -res.depth, 'b', 'LineWidth', 2);
    xlabel(ax, panels{k, 4});
    ylabel(ax, 'Depth (m)');
    title(ax, sprintf('%s %s (%s)', panels{k, 5}, st.label, st.cast));
    legend(ax, {'CTD', 'GLORYS raw', 'GLORYS corrected'}, 'Location', 'best');
    grid(ax, 'on');
    box(ax, 'on');
end

if nargin > 1 && ~isempty(out_dir)
    if ~exist(out_dir, 'dir'), mkdir(out_dir); end
    print(fig, fullfile(out_dir, ['profiles_' st.label '.png']), '-dpng', '-r300');
end
end
