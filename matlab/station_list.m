function stations = station_list()
%STATION_LIST Stations S1-S6: identifiers and file names.
%
%   Station  CTD file        GLORYS extract               Figure label
%   S1       NF003_008.cnv   GLORYS_Raw_Station_008.csv   Station-01
%   S2       NF003_009.cnv   GLORYS_Raw_Station_009.csv   Station-02
%   S3       NF003_010.cnv   GLORYS_Raw_Station_010.csv   Station-03
%   S4       NF003_012.cnv   GLORYS_Raw_Station_012.csv   Station-04
%   S5       NF003_013.cnv   GLORYS_Raw_Station_013.csv   Station-05
%   S6       NF003_014.cnv   GLORYS_Raw_Station_014.csv   Station-06
%
%   File names are relative to the data folder (data/raw).

file_ids = {'08', '09', '10', '12', '13', '14'};
stations = struct('key', {}, 'cast', {}, 'label', {}, ...
                  'ctd_file', {}, 'glorys_file', {});
for k = 1:numel(file_ids)
    stations(k).key = sprintf('S%d', k);
    stations(k).cast = ['NF003_0' file_ids{k}];
    stations(k).label = sprintf('Station-%02d', k);
    stations(k).ctd_file = fullfile('ctd', [stations(k).cast '.cnv']);
    stations(k).glorys_file = fullfile('glorys', ...
        ['GLORYS_Raw_Station_0' file_ids{k} '.csv']);
end
end
