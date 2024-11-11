VIDEO1 = "JohnMaeda_Simplicity";
VIDEO2 = "Training_Day";
VIDEO3 = "The_Carbon_Connection";

var videoImageSet = [VIDEO1+".png", VIDEO2+".png", VIDEO3+".png"];
var videoSet = [VIDEO1+".mp4", VIDEO2+".mp4", VIDEO3+".mp4"];
var videoArrayLength = videoSet.length;

$('#myimage-1,#myimage-2,#myimage-3').bind('click', function () {
  for (var i = 1; i <= 3; i++) {
    $('#myimage-'+i).removeClass('box');
    $('#video-title-'+i).removeClass('box-title');
  }
  var activeVideo = $(this).attr('id').split('-');
  var s = "my-video-" + activeVideo[1];
  var strSrc = document.getElementById(s).src;

  $( this ).addClass("box");
  $('#video-title-'+ activeVideo[1] ).addClass('box-title');

  var $myVideo = $("#my-video");
  $myVideo.attr("src", strSrc);
  $myVideo.attr("data-vid", activeVideo[1]);
  $myVideo.get(0).load();
  $myVideo.get(0).play();
});

$('#my-video').click(function() {
  if (this.paused === false) {
      this.pause();
  } else {
      this.play();
  }
});

$('#my-video-1, #my-video-2, #my-video-3, #my-video').hover(function toggleControls() {
  if (this.hasAttribute("controls")) {
      this.removeAttribute("controls")
  } else {
      this.setAttribute("controls", "controls")
  }
  for (var i = 1; i <= 3; i++) {
    $('#myimage-'+i).removeClass('box');
    $('#video-title-'+i).removeClass('box-title');
  }
  $('#video-title-'+ this.getAttribute("data-vid")).addClass('box-title');
  $('#myimage-'+ this.getAttribute("data-vid")).addClass('box');
});

var bindOnload = function (xhr, i) {
  xhr.onload = function (e) {
    if (this.status === 200) {
      var myBlob = this.response;
      var vid = (window.URL ? window.URL : window.webktURL).createObjectURL(myBlob);
      var video = document.getElementById('my-video-' + ++i);
      video.src = vid;
      video.setAttribute('poster', "img/"+videoImageSet[--i]);
      var image = document.getElementById('myimage-' + ++i);
      image.src = "img/"+videoImageSet[--i];
      VIDEOSET = {video: "img/"+videoImageSet[--i]}
    }
    else {
      console.log("error: " + e);
    }
  };
};

for (var i = 0; i < videoArrayLength; i++) {
  var xhr = new XMLHttpRequest();
  xhr.open('GET', '/api/Video/starter/' + videoSet[i], true);
  xhr.responseType = 'blob';
  bindOnload(xhr, i);
  xhr.send();
}
for (var a = 0, b = 1; a < videoArrayLength; a++, b++) {
  var s = videoSet[a];
  s = videoSet[a].substring(0, s.indexOf('.'));
  $('#video-title-' + b).text(s).fadeIn(5000);
}
/* functions */
function postProcessVideo(position, video) {
    const source = new EventSource('/stream');

  source.onmessage = event => {
    const data_pack = JSON.parse(event.data);

    const serverDataSpeech = document.getElementById("serverDataSpeech");
    const serverDataSpeechPlaceholder = document.getElementById("serverDataSpeechPlaceholder");

    if (serverDataSpeechPlaceholder.innerHTML !== data_pack['speech1'] && data_pack['speech1'] !== "") {
      serverDataSpeech.innerHTML = `${data_pack['speech1']}<br>${serverDataSpeech.innerHTML}`;
    }

    serverDataSpeechPlaceholder.innerHTML = data_pack['speech1'];
  };

  const url = "/api/Process";
  const dat = {"videoName": video};

  $(`.group-${position} span.not-loading`).fadeIn(5000).addClass("loading");
  $(`.group-${position} button`).remove();

  $.post(url, dat)
    .done(data => {
      const $notLoading = $(`.group-${position} span.not-loading`);
      $notLoading.append(`<span class="loaded-two btn-notice">${data}</span>`);

      if ($(".loaded-one")) {
        $notLoading.removeClass("loading");
        source.close();
      }
    })
    .fail(data => {
      const $notLoading = $(`.group-${position} span.not-loading`);
      $notLoading.removeClass("loading");
      $notLoading.append(`<button class="loaded-two btn-notice btn-sm">${data}</button>`);
    });
}

function postWordList() {
  var url = "/api/Words";
  var dat = {};
  dat['word1'] = document.getElementById('searchinput').value;
  for (var videoString = 1; videoString <= this.videoArrayLength; videoString++) {
    dat['v'+videoString] = document.getElementById('video-title-'+videoString).innerHTML;
  }
  for (var feed = 1; feed <= this.videoArrayLength; feed++) {
    $('#search-feed').empty();
  }
  if (dat['word1'] == "") {
    return
  }
  $.post(url, dat, function (data) {
    })
    .done(function (data) {
      vt1 = document.getElementById('video-title-1').innerHTML;
      vt2 = document.getElementById('video-title-2').innerHTML;
      vt3 = document.getElementById('video-title-3').innerHTML;
      $myWord1 = $('#search-feed');
      var wordPack = $.parseJSON(data);

      $.each( wordPack, function( key, value ) {
        var keySplit = key.split('-');
        var valueSplit = value.split('-');
        var glyph = (valueSplit[1] === "tag" ? valueSplit[1] : "user");
        if (keySplit[0] === vt1)
          var buttonString1 = '<div onmouseover="hoverSkit(1)" onclick="postSecond(1, ' + keySplit[1] + ')" ' +
            'class="row btn-skittle btn-'+ valueSplit[1] +'" data-vid="1" data-sec="'+keySplit[1]+'">' +
            '<span class="col-xs-1 glyphicon glyphicon-'+ glyph +' glyph-'+ glyph +'"></span> ' +
            '<span class="col-xs-10 link-text-body">'+ valueSplit[0] +'</span>' +
            '<span class="col-xs-1 btn-span"> '+keySplit[1]+' s</span></div>';
          $myWord1.prepend(buttonString1);
        if (keySplit[0] === vt2)
          var buttonString2 = '<div onmouseover="hoverSkit(2)" onclick="postSecond(2, ' + keySplit[1] + ')" ' +
            'class="row btn-skittle btn-'+ valueSplit[1] +'" data-vid="2" data-sec="'+keySplit[1]+'">' +
            '<span class="col-xs-1 glyphicon glyphicon-'+ glyph +' glyph-'+ glyph +'"></span> ' +
            '<span class="col-xs-10 link-text-body">'+ valueSplit[0] +'</span>' +
            '<span class="col-xs-1 btn-span"> '+keySplit[1]+' s</span></div>';
          $myWord1.prepend(buttonString2);
        if (keySplit[0] === vt3)
          var buttonString3 = '<div onmouseover="hoverSkit(3)" onclick="postSecond(3, ' + keySplit[1] + ')" ' +
            'class="row btn-skittle btn-'+ valueSplit[1] +'" data-vid="3" data-sec="'+keySplit[1]+'">' +
            '<span class="col-xs-1 glyphicon glyphicon-'+ glyph +' glyph-'+ glyph +'"></span> ' +
            '<span class="col-xs-10 link-text-body">'+ valueSplit[0] +'</span>' +
            '<span class="col-xs-1 btn-span"> '+keySplit[1]+' s</span></div>';
          $myWord1.prepend(buttonString3);
      });

      // Sort the tag/dialogs returned
      var superSort = function(w) {
        w.find('.btn-skittle').sort(function(a, b) {
          return +a.getAttribute('data-sec') - +b.getAttribute('data-sec');
        }).appendTo(w);
        return w;
      };
      superSort($myWord1);
    })
    .fail(function () {
      alert("fail!")
    });
}

$(document).keyup(function(e){
  if (e.which === 13 || e.which === 46 || e.which === 8){
    $("#post-word-list").click();
  }
  if (e.keyCode >= 65 && e.keyCode <= 90) {
    $("#post-word-list").click();
  }
});

const postSecond = (video, second) => {
  const obj = {video, second};
  for (let i = 1; i <= 3; i++) {
    $(`#myimage-${i}`).removeClass('box');
    $(`#video-title-${i}`).removeClass('box-title');
  }
  $(`#myimage-${obj.video}`).addClass('box');
  $(`#video-title-${obj.video}`).addClass('box-title');

  const s = `my-video-${obj.video}`;
  const strSrc = document.getElementById(s).src;
  const $myVideo = $("#my-video");
  $myVideo.attr("src", strSrc).attr("data-vid", obj.video);

  $myVideo.get(0).load();
  $myVideo.get(0).currentTime = obj.second;
  $myVideo.get(0).play();
}

// Bind hover effect
const hoverSkit = (movie) => {
  for (let i = 1; i <= 3; i++) {
    $(`#myimage-${i}`).removeClass('box');
    $(`#video-title-${i}`).removeClass('box-title');
  }
  $(`#video-title-${movie}`).addClass('box-title');
  $(`#myimage-${movie}`).addClass('box');
}