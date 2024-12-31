// Initialize VIDEOSET
var VIDEOSET = {};

// Update the videoImageSet and videoSet arrays based on the global variables
var videoImageSet = [VIDEO1 + ".png", VIDEO2 + ".png", VIDEO3 + ".png"];
var videoSet = [VIDEO1 + ".mp4", VIDEO2 + ".mp4", VIDEO3 + ".mp4"];
var videoArrayLength = videoSet.length;

// Bind click event to video images
$('#myimage-1,#myimage-2,#myimage-3').bind('click', function () {
    for (var i = 1; i <= 3; i++) {
        $('#myimage-' + i).removeClass('box');
        $('#video-title-' + i).removeClass('box-title');
    }
    var activeVideo = $(this).attr('id').split('-');
    var s = "my-video-" + activeVideo[1];
    var videoElement = document.getElementById(s);
    if (!videoElement) {
        console.error(`Video element with ID '${s}' not found.`);
        return;
    }
    var strSrc = videoElement.src;

    $(this).addClass("box");
    $('#video-title-' + activeVideo[1]).addClass('box-title');

    var $myVideo = $("#my-video");
    $myVideo.attr("src", strSrc);
    $myVideo.attr("data-vid", activeVideo[1]);
    $myVideo.get(0).load();
    $myVideo.get(0).play();
});

// Toggle play/pause on video click
$('#my-video').click(function () {
    if (this.paused === false) {
        this.pause();
    } else {
        this.play();
    }
});

// Toggle controls on hover
$('#my-video-1, #my-video-2, #my-video-3, #my-video').hover(function toggleControls() {
    if (this.hasAttribute("controls")) {
        this.removeAttribute("controls")
    } else {
        this.setAttribute("controls", "controls")
    }
    for (var i = 1; i <= 3; i++) {
        $('#myimage-' + i).removeClass('box');
        $('#video-title-' + i).removeClass('box-title');
    }
    $('#video-title-' + this.getAttribute("data-vid")).addClass('box-title');
    $('#myimage-' + this.getAttribute("data-vid")).addClass('box');
});

// Bind onload to handle video and image setup
var bindOnload = function (xhr, i) {
    xhr.onload = function (e) {
        if (this.status === 200) {
            var myBlob = this.response;
            var vid = (window.URL ? window.URL : window.webkitURL).createObjectURL(myBlob);

            var videoIndex = i + 1; // Assuming i starts at 0

            // Get the video element
            var video = document.getElementById('my-video-' + videoIndex);
            if (video) {
                video.src = vid;
                video.setAttribute('poster', "img/" + videoImageSet[i]);
            } else {
                console.error(`Video element with ID 'my-video-${videoIndex}' not found.`);
            }

            // Get the image element
            var image = document.getElementById('myimage-' + videoIndex);
            if (image) {
                image.src = "img/" + videoImageSet[i];
            } else {
                console.error(`Image element with ID 'myimage-${videoIndex}' not found.`);
            }

            // Update VIDEOSET (ensure VIDEOSET is defined elsewhere)
            if (typeof VIDEOSET !== 'undefined') {
                VIDEOSET[`video${videoIndex}`] = "img/" + videoImageSet[i];
            } else {
                console.warn("VIDEOSET is not defined.");
            }
        }
        else {
            console.log("error: " + e);
        }
    };
};

// Fetch and bind video sources
for (var i = 0; i < videoArrayLength; i++) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/Video/starter/' + videoSet[i], true);
    xhr.responseType = 'blob';
    bindOnload(xhr, i);
    xhr.send();
}

// Update video titles
for (var a = 0; a < videoArrayLength; a++) {
    var s = videoSet[a].substring(0, videoSet[a].indexOf('.'));
    $('#video-title-' + (a + 1)).text(s).fadeIn(5000);
}

/* functions */

// Function to process video and handle SSE messages
function postProcessVideo(position, video) {
    const source = new EventSource('/stream');

    source.onmessage = event => {
        try {
            const data_pack = JSON.parse(event.data);

            const serverDataSpeech = document.getElementById("serverDataSpeech");
            const serverDataSpeechPlaceholder = document.getElementById("serverDataSpeechPlaceholder");

            if (data_pack.type === "transcription") {
                const transcription = `[${data_pack.clip}] ${data_pack.text}`;
                if (serverDataSpeechPlaceholder.innerHTML !== transcription && transcription !== "") {
                    serverDataSpeech.innerHTML = `${transcription}<br>${serverDataSpeech.innerHTML}`;
                }
                serverDataSpeechPlaceholder.innerHTML = transcription;
            } else if (data_pack.type === "info") {
                const infoMessage = `INFO: ${data_pack.text}`;
                serverDataSpeech.innerHTML = `${infoMessage}<br>${serverDataSpeech.innerHTML}`;
            } else if (data_pack.type === "error") {
                const errorMessage = `ERROR: [${data_pack.clip}] ${data_pack.text}`;
                serverDataSpeech.innerHTML = `${errorMessage}<br>${serverDataSpeech.innerHTML}`;
            } else {
                // Handle any other message types if necessary
                console.warn("Unknown message type:", data_pack.type);
            }
        } catch (e) {
            console.error("Failed to parse SSE message as JSON:", e);
            console.error("Received data:", event.data);
        }
    };

    const url = "/api/Process";
    const dat = { "videoName": video };

    $(`.group-${position} span.not-loading`).fadeIn(5000).addClass("loading");
    $(`.group-${position} button`).remove();

    $.post(url, dat)
        .done(data => {
            const $notLoading = $(`.group-${position} span.not-loading`);
            // Check if the status is completed
            if (data.status === "completed") {
                $notLoading.removeClass("loading");
                $notLoading.html(`<span class="btn-notice btn-success">${data.message}</span>`);
                source.close();
            } else {
                $notLoading.append(`<span class="loaded-two btn-notice">${data.message}</span>`);
            }
        })
        .fail(data => {
            const $notLoading = $(`.group-${position} span.not-loading`);
            $notLoading.removeClass("loading");
            // Display error message from backend if available
            const errorMsg = data.responseJSON?.error || "An error occurred.";
            $notLoading.html(`<span class="btn-notice btn-danger">${errorMsg}</span>`);
            source.close();
        });
}

// Function to perform search
function postWordList() {
    var url = "/api/Words";
    var dat = {};
    dat['word1'] = document.getElementById('searchinput').value;
    for (var videoString = 1; videoString <= videoArrayLength; videoString++) {
        dat['v' + videoString] = document.getElementById('video-title-' + videoString).innerHTML;
    }
    for (var feed = 1; feed <= videoArrayLength; feed++) {
        $('#search-feed').empty();
    }
    if (dat['word1'] == "") {
        return;
    }
    $.ajax({
        url: url,
        method: "POST",
        data: dat,
        dataType: "json", // Ensure the response is treated as JSON
        success: function (data) {
            const vt1 = document.getElementById('video-title-1').innerHTML;
            const vt2 = document.getElementById('video-title-2').innerHTML;
            const vt3 = document.getElementById('video-title-3').innerHTML;
            const $myWord1 = $('#search-feed');

            // 'data' is already a JavaScript object
            $.each(data, function (key, value) {
                var keySplit = key.split('-');
                var valueSplit = value.split('-');
                var glyph = (valueSplit[1] === "tag" ? "tag" : "user"); // Ensure correct glyph class
                var videoTitle = keySplit[0];
                var videoSec = keySplit[1];
                var videoNumber = getVideoNumber(videoTitle);
                var btnClass = `btn-skittle btn-${valueSplit[1]}`;
                var btnHtml = `
                    <div onmouseover="hoverSkit(${videoNumber})" 
                         onclick="postSecond(${videoNumber}, ${videoSec})" 
                         class="row ${btnClass}" data-vid="${videoNumber}" data-sec="${videoSec}">
                        <span class="col-xs-1 glyphicon glyphicon-${glyph} glyph-${glyph}"></span>
                        <span class="col-xs-10 link-text-body">${valueSplit[0]}</span>
                        <span class="col-xs-1 btn-span">${videoSec} s</span>
                    </div>`;

                if (videoTitle === vt1 || videoTitle === vt2 || videoTitle === vt3) {
                    $myWord1.prepend(btnHtml);
                }
            });

            // Sort the tag/dialogs returned
            var superSort = function (w) {
                w.find('.btn-skittle').sort(function (a, b) {
                    return +a.getAttribute('data-sec') - +b.getAttribute('data-sec');
                }).appendTo(w);
                return w;
            };
            superSort($myWord1);
        },
        error: function () {
            alert("Search failed!");
        }
    });
}

// Helper function to get video number based on title
function getVideoNumber(title) {
    for (let i = 1; i <= videoArrayLength; i++) {
        if (document.getElementById('video-title-' + i).innerHTML === title) {
            return i;
        }
    }
    return 1; // Default to 1 if not found
}

// Bind keyup events for search input
$(document).keyup(function (e) {
    if (e.which === 13 || e.which === 46 || e.which === 8) {
        $("#post-word-list").click();
    }
    if (e.keyCode >= 65 && e.keyCode <= 90) {
        $("#post-word-list").click();
    }
});

// Function to jump to a specific second in a video
const postSecond = (video, second) => {
    const obj = { video, second };
    for (let i = 1; i <= 3; i++) {
        $(`#myimage-${i}`).removeClass('box');
        $(`#video-title-${i}`).removeClass('box-title');
    }
    $(`#myimage-${obj.video}`).addClass('box');
    $(`#video-title-${obj.video}`).addClass('box-title');

    const s = `my-video-${obj.video}`;
    const videoElement = document.getElementById(s);
    if (!videoElement) {
        console.error(`Video element with ID '${s}' not found.`);
        return;
    }
    const strSrc = videoElement.src;
    const $myVideo = $("#my-video");
    $myVideo.attr("src", strSrc).attr("data-vid", obj.video);

    $myVideo.get(0).load();
    $myVideo.get(0).currentTime = obj.second;
    $myVideo.get(0).play();
}

// Function to handle hover effects
const hoverSkit = (movie) => {
    for (let i = 1; i <= 3; i++) {
        $(`#myimage-${i}`).removeClass('box');
        $(`#video-title-${i}`).removeClass('box-title');
    }
    $(`#video-title-${movie}`).addClass('box-title');
    $(`#myimage-${movie}`).addClass('box');
}
