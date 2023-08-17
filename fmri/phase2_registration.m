
%set data directory
data_dir= 'E:\dhcp_analysis_full';
git_dir = 'C:\Users\ArcaroLab\Desktop\git_repos\dhcp';

%load sub_list
sub_list = readtable([data_dir,'/participants.csv']);


%loop through subs and start conversion
for sub_ind = 1:height(sub_list)
    
    sub = sub_list.participant_id(sub_ind);
    ses = sub_list.ses(sub_ind);

    

    sub_dir = [data_dir,'/',sub{1},'/',ses{1},'/surf'];

    %check if sub directory exists and if sub_list.phase_2 is not 1
    if exist(sub_dir) == 7 && sub_list.phase_1(sub_ind) == 1 && sub_list.phase_2(sub_ind) ~= 1
        disp(['Processing ',sub_ind, ' ', sub{1}])
        try
            cd(sub_dir)
    
            %write lh curv data
            lh_curv=gifti('lh_curv.txt');
            lh_curv.cdata=-lh_curv.cdata;
            write_curv(['lh.curv'],lh_curv.cdata,length(lh_curv.cdata));
            
            %write lh sulc data
            lh_sulc=gifti('lh_sulc.txt');
            lh_sulc.cdata=-lh_sulc.cdata;
            write_curv(['lh.sulc'],lh_sulc.cdata,length(lh_sulc.cdata));
            
            %write rh curv data
            rh_curv=gifti('rh_curv.txt');
            rh_curv.cdata=-rh_curv.cdata;
            write_curv(['rh.curv'],rh_curv.cdata,length(rh_curv.cdata));
            
            %write rh sulc data
            rh_sulc=gifti('rh_sulc.txt');
            rh_sulc.cdata=-rh_sulc.cdata;
            write_curv(['rh.sulc'],rh_sulc.cdata,length(rh_sulc.cdata));

            %add 1 to phase 2 column
            sub_list.phase_2(sub_ind) = 1;
        catch
            fileID = fopen([git_dir,'/fmri/qc/','preproc_log.txt'], 'a');
            data = ['Error in phase2_registration.m for ', sub{1}];
            fprintf(fileID, '%s\n', data);
            fclose(fileID);



        end




    end


end

%save updated sub_list
writetable(sub_list,[data_dir,'/participants.csv']);




