$(document).ready(function() {
    "use strict";

    /******************** NAVBAR ********************/
    var animationProp = $('.navbar-nemo'); //Navbar wraper
    var scrollPos = $(this).scrollTop(),
        animationEndPos = 150,
        logo = animationProp.find('.navbar-brand img');

    if (animationProp.hasClass('navbar-transparent') && matchMedia('only screen and (min-width: 769px)').matches) {
        //if visitor refresh on the middle of the document
        if (scrollPos > animationEndPos) {
            animationProp.removeClass('navbar-transparent');
            logo.attr('src', 'static/images/fo-base.png');
        }

        //toggle existing class
        $(document).scroll(function() {
            scrollPos = $(this).scrollTop();
            if (scrollPos > animationEndPos) {
                animationProp.removeClass('navbar-transparent');
                logo.attr('src', 'static/images/fo-base.png');
            } else {
                animationProp.addClass('navbar-transparent');
                logo.attr('src', 'static/images/fo-alt.png');
            }
        });
    } else {
        logo.attr('src', 'static/images/fo-base.png');
    }

    /******************** TYPED ********************/
    $(function() {
        $(".element").typed({
            strings: ["Échangez", "Rencontrez", "Recrutez"],
            typeSpeed: 50,
            backSpeed: 100,
            backDelay: 1000,
        });
    });

    /******************** BACKGROUND VIDEO ********************/
    var vidContainer1 = document.querySelector(".video-player");
    var vidContainer2 = document.querySelector(".the-video-2");

    if (vidContainer1 != null) {
        var vid = vidContainer1.querySelector("video");
        var pauseButton = vidContainer1.querySelector("button");

        vid.addEventListener('ended', function() {
            // only functional if "loop" is removed
            vid.pause();
            // to capture IE10
            // vidFade();
        });

        pauseButton.addEventListener("click", function() {
            if (vid.paused) {
                vid.play();
                $(pauseButton).animate({
                    'bottom': '50px',
                    'opacity': '0.5'
                });
                $(pauseButton).find('.play').removeClass('active');
                $(pauseButton).find('.pause').addClass('active');

            } else {
                vid.pause();
                $(pauseButton).animate({
                    'bottom': '50%',
                    'opacity': '1'
                });
                $(pauseButton).find('.pause').removeClass('active');
                $(pauseButton).find('.play').addClass('active');
            }
        });
    }

    if (vidContainer2 != null) {
        var vid = vidContainer2.querySelector("video");
        var pauseButton = vidContainer2.querySelector("button");

        vid.addEventListener('ended', function() {
            // only functional if "loop" is removed
            vid.pause();
            // to capture IE10
            // vidFade();
        });

        pauseButton.addEventListener("click", function() {
            if (vid.paused) {
                vid.play();
                $(vidContainer2).addClass('playing');
                $(pauseButton).find('.play').removeClass('active');
                $(pauseButton).find('.pause').addClass('active');

            } else {
                vid.pause();
                $(vidContainer2).removeClass('playing');
                $(pauseButton).animate({
                    'bottom': '50%',
                    'opacity': '1'
                });
                $(pauseButton).find('.pause').removeClass('active');
                $(pauseButton).find('.play').addClass('active');
            }
        });
    }

    /******************** NAVBAR APPEAR ON SCROLL ********************/
    if (animationProp.hasClass('appear-onscroll')) {
        $(document).scroll(function() {
            var scrollPos = $(this).scrollTop();

            if (scrollPos > 150) {
                animationProp.removeClass('appear-onscroll');
            } else {
                animationProp.addClass('appear-onscroll');
            }
        });
    }

    /******************** ONE PAGE NAVIGATION ********************/
    $('.navbar-nav').onePageNav({
        currentClass: 'active',
        scrollOffset: 74
    });

    /******************** SCROLL HACK ********************/
    $(window).scroll(function() {
        if ($(this).scrollTop() > 50) {
            $('.navbar-nav').addClass('opaque');
        } else {
            $('.navbar-nav').removeClass('opaque');
        }
    });

    /****************** MAP *******************************/
    var initMapBig = function() {
        var map = new google.maps.Map(document.getElementById('mapBig'), {
            zoom: 17,
            center: {
                lat: 45.7811929,
                lng: 4.8720335
            },
            scrollwheel: false
        });

        var contentString = '<div class="map-info-window">' +
            '<h3 id="edit3" class="title-text">Forum Rhône-Alpes - Double Mixte</h3>' +
            '<address>' +
            '<p id="edit1">19 Avenue Gaston Berger, 69100 Villeurbanne</p>' +
            '</address>' +
            '</div>';

        var infowindow = new google.maps.InfoWindow({
            content: contentString,
            maxWidth: 318,
            borderRadius: 4,
            backgroundColor: '#ffffff',
            hideCloseButton: true,
            borderWidth: 0,
            shadowStyle: 0,
            disableAutoPan: false
        });

        var marker = new google.maps.Marker({
            position: {
                lat: 45.780469,
                lng: 4.871804
            },
            map: map,
            title: 'Forum Rhône-Alpes'
        });

        marker.addListener('click', function() {
            infowindow.open(map, marker);
        });
        infowindow.open(map, marker);
    }

    if (document.getElementById('mapBig') != null) {
        initMapBig();
    }

    /******************** SCROLLTO ********************/
    $('a[href^="#"]').click(function(e) {
        e.preventDefault();
        $(window).stop(true).scrollTo(this.hash, {
            duration: 750,
            interrupt: true
        });
    });

    /******************** CONTACT FORM ********************/
    function validateEmail(email) {
        var re = /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,6}(?:\.[a-z]{2})?)$/i;
        return re.test(email);
    }

    $('#contact-form').on('submit', function(e) {
        e.preventDefault();
        var error_msg = $(this).find('.error-msg');
        var success_msg = $(this).find('.success-msg');
        var data = {
            nom_complet: $(this).find('input[name="nom_complet"]').val(),
            nom: $(this).find('input[name="nom"]').val(),
            tel: $(this).find('input[name="tel"]').val(),
            email: $(this).find('input[name="email"]').val(),
            captcha: grecaptcha.getResponse()
        }

        if (validateEmail(data.email) && data.nom && data.tel && data.nom_complet && data.captcha) {
            $.ajax({
                type: "GET",
                url: $(this).attr('action'),
                data: data,
                success: function() {
                    $("#send_mail").prop('disabled', true);
                    success_msg.fadeIn(500);
                    error_msg.fadeOut(500);
                },
                error: function() {
                    $("#send_mail").prop('enabled', true);
                    error_msg.fadeIn(500);
                    alert('Veuillez cocher la case \'Je ne suis pas un robot\'');
                    success_msg.fadeOut(500);
                }
            });
        } else {
            $("#send_mail").prop('enabled', true);
            error_msg.fadeIn(500);
            success_msg.fadeOut(500);
        }

        return false;
    });

});
