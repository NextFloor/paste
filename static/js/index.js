AWS.config.update({
    region: bucketRegion,
    credentials: new AWS.CognitoIdentityCredentials({
        IdentityPoolId: identityPoolId
    })
});

var s3 = new AWS.S3({
    apiVersion: '2006-03-01',
    params: {Bucket: bucketName}
});

var isFileTransfer = function(dt) {
    return (
        !$.trim($("#source").val()) &&
        (dt.types && (dt.types.indexOf ? dt.types.indexOf('Files') !== -1 : dt.types.contains('Files')))
    );
};

$(function() {
    $('#highlighting').select2();
    $('#expiration').select2({minimumResultsForSearch: Infinity});

    $('form').bind('submit', function () {
        $(this).find(':input').prop('disabled', false);
    });

    $('#source').on('drag dragstart dragend dragover dragenter dragleave drop', function (e) {
        if (isFileTransfer(e.originalEvent.dataTransfer)) {
            e.preventDefault();
            e.stopPropagation();
        }
    }).on('dragenter dragover', function (e) {
        if (isFileTransfer(e.originalEvent.dataTransfer)) {
            $('.source-upload-overlay').fadeIn('fast');
            $('.source').blur().prop('readonly', true);
        }
    }).on('dragleave dragend', function (e) {
        if (isFileTransfer(e.originalEvent.dataTransfer)) {
            if (e.target !== e.relatedTarget) {
                $('.source-upload-overlay').fadeOut('fast');
                $('.source').prop('readonly', false);
            }
        }
    }).on('drop', function (e) {
        var dt = e.originalEvent.dataTransfer;

        if (!isFileTransfer(dt)) {
            return;
        }

        var file = dt.files[0];

        if (dt.files.length > 1 || (!file.type && file.size % 4096 === 0 && file.size <= 102400)) {
            $('.source-upload-overlay').fadeOut('fast');
            $('.source').prop('readonly', false);

            alert('파일을 1개만 올려주세요.');
            return;
        }

        $('#source')
            .prop('placeholder', '')
            .text('\u200b');

        $('#source-upload-overlay-status').html('업로드 준비 중...');
        $('.source-upload-overlay').css('pointer-events', 'auto');
        $('#highlighting')
            .val('auto').trigger('change.select2')
            .prop('disabled', true);
        $('#submit-button').prop('disabled', true);
        $('#title').val(file.name);

        $.ajax({
            url: '/x/k',
            method: 'POST',
            dataType: 'json'
        }).done(function(data) {
            var key = data.key;
            s3.upload({
                Key: key,
                Body: file,
                ContentDisposition: 'attachment; filename="' + encodeURIComponent(file.name) + '"'
            }, function (err) {
                if (err) {
                    alert('upload error');
                    console.log(err);
                } else {
                    $('.source-upload-overlay').addClass('source-upload-overlay-green');
                    $('.source-upload-overlay-icon').removeClass('fa-cloud-upload').addClass('fa-check');
                    $('#source-upload-overlay-status').html('업로드 완료!<br>하단 정보를 기입하고 만들기 버튼을 눌러주세요.');
                    $('#resource').val(key);
                    $('#submit-button').prop('disabled', false);
                }
            }).on('httpUploadProgress', function (progress) {
                var percentage = Math.round((progress.loaded / progress.total) * 100);
                var mbLoaded = (progress.loaded / 1000 / 1000).toFixed(2);
                var mbTotal = (progress.total / 1000 / 1000).toFixed(2);
                $('#source-upload-overlay-status').html('업로드 중...<br>(' + mbLoaded + ' / ' + mbTotal + ' MB, ' + percentage + '%)');
            });
        }).fail(function(xhr, err) {
            alert('generate key error');
            console.log(err);
        });
    });
});
