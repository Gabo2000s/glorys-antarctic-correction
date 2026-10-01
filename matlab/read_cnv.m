function cast = read_cnv(file)
%READ_CNV Read a Sea-Bird .cnv file.
%   CAST = READ_CNV(FILE) returns a structure with
%     latitude, longitude  NMEA position from the header, in signed decimal
%                          degrees (south and west negative)
%     <channel>            one column vector per channel, named after the
%                          short channel name in the header (depSM, tv290C,
%                          sal00, c0S_m, flag)
%   Values equal to the header's bad_flag are returned as NaN.
%
%   The header position and time are the confirmed station position and
%   time, also listed in data/stations.csv. The correction uses the header
%   position.

fid = fopen(file, 'rt');
if fid < 0
    error('read_cnv:open', 'Cannot open %s', file);
end
closer = onCleanup(@() fclose(fid));

names = {};
bad_flag = NaN;
cast.latitude = NaN;
cast.longitude = NaN;

% Header
line = fgetl(fid);
while ischar(line)
    if strcmp(strtrim(line), '*END*')
        break
    end
    tok = regexp(line, '^#\s*name\s+(\d+)\s*=\s*([^:]+):', 'tokens', 'once');
    if ~isempty(tok)
        names{str2double(tok{1}) + 1} = matlab.lang.makeValidName(strtrim(tok{2}));
    end
    tok = regexp(line, '^#\s*bad_flag\s*=\s*(\S+)', 'tokens', 'once');
    if ~isempty(tok)
        bad_flag = str2double(tok{1});
    end
    tok = regexp(line, '^\*\s*NMEA Latitude\s*=\s*(\d+)\s+([\d.]+)\s*([NS])', ...
                 'tokens', 'once', 'ignorecase');
    if ~isempty(tok)
        cast.latitude = signed_degrees(tok, 'S');
    end
    tok = regexp(line, '^\*\s*NMEA Longitude\s*=\s*(\d+)\s+([\d.]+)\s*([EW])', ...
                 'tokens', 'once', 'ignorecase');
    if ~isempty(tok)
        cast.longitude = signed_degrees(tok, 'W');
    end
    line = fgetl(fid);
end

% Data
data = textscan(fid, repmat('%f', 1, numel(names)), 'CollectOutput', true);
data = data{1};
if isempty(data)
    error('read_cnv:nodata', '%s: no data found after *END*', file);
end
if isfinite(bad_flag)
    data(abs(data - bad_flag) <= abs(bad_flag) * 1e-6) = NaN;
end
for k = 1:numel(names)
    cast.(names{k}) = data(:, k);
end
end


function value = signed_degrees(tok, negative_hemisphere)
value = str2double(tok{1}) + str2double(tok{2}) / 60;
if strcmpi(tok{3}, negative_hemisphere)
    value = -value;
end
end
