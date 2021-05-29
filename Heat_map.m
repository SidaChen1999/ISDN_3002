% Enter your MATLAB code below
strength = [-43 -47 -63 -60 -61 -56 -57 -61 -55 -50 -55 -54 -55]';
% strength = thingSpeakRead(1399076, 'ReadKey', '9G5RZ4FNZD3KWFV1','numPoints',13 ,'fields',[1]);
% X = [748 670 592 514 432 357 275 197 118 40 40 118 197 275 357 432 514 592 670 748]'; %880
% Y = [513 513 513 513 513 513 513 513 513 513 435 435 435 435 435 435 435 435 435 435]'; %586
X = [709 551 393 237 79 237 393 551 709 709 551 393 237]';
Y = [472 472 472 472 472 315 315 315 315 157 157 157 157]';

strengthPercent = 2*(strength+100)/100;
% picture = imread('https://i.ibb.co/bvGJzCN/Floor-Plan-Small.jpg'); 
picture = imread('Floor_Plan_Small.jpg');
[height,width,depth] = size(picture);

OverlayImage=[];
F = scatteredInterpolant(Y, X, strengthPercent,'linear');
for i = 1:height-1
   for j = 1:width-1
          OverlayImage(i,j) = F(i,j);
   end
end
alpha = (~isnan(OverlayImage))*0.6;

imshow(picture);
hold on
OverlayImage = imshow( OverlayImage );
caxis auto  
colormap( OverlayImage.Parent, jet );
colorbar( OverlayImage.Parent );
set( OverlayImage, 'AlphaData', alpha );
for i = 1:length(X)
   text(X(i), Y(i), string(strength(i))); 
end
hold off