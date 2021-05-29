a = [1, 2, 3, 4, 5, 6, 7];
d1 = [37 36 38];
d2 = [48 43 41 45 43 43 40];
d3 = [51 47 49 49 51 50 47 48 49];
d4 = [55 55 55 53 54 52 50 53 50];
d5 = [54 52 51 54 52 52 54 ];
d6 = [52 54 53 52 52 54 52 51 52 ];
d7 = [52 48 53 55 51 55 54 50 ];

distance = zeros(1,60);
MHz = 2400;
FSPL = 27.55;
for dBm = 1:60
    m = 10 ^ (( FSPL - (20 * log10(MHz)) + dBm ) / 20 );
    m = round(m,2);
    distance(dBm) = m;
end
distance2 = zeros(1,60);
A = -36;
n = 2.5;
for dBm = 1:60
    m2 = 10 ^ ((A + dBm) / (10 * n));
    m2 = round(m2, 2);
    distance2(dBm) = m2;
end
% m = 10 ^ (( FSPL - (20 * math.log10(MHz)) + dBm ) / 20 );
% m = round(m,2);
figure; hold on;
plot(1:60, distance);
plot(1:60, distance2, 'g')
xlabel('dBm');ylabel('m');
plot(d1, 1, 'r.');
plot(d2, 2, 'r.');
plot(d3, 3, 'r.');
plot(d4, 4, 'r.');
plot(d5, 5, 'r.');
plot(d6, 6, 'r.');
plot(d7, 7, 'r.');
hold off;
