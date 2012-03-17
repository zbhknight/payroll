
function goLite(input){
	$(input).css({background:"#EEEEF4",color:"#6666AA",border:"#9999DD"})
}

function goDim(input){
	$(input).css({background:"#EEEEEE",color:"#888888",border:"solid 1px #BBBBBB"})
}

$(document).ready(function() {
		$(":button").live("mouseover", function() {goLite(this)})
		$(":button").live("mouseout", function() {goDim(this)})
		$(":submit").live("mouseover", function() {goLite(this)})
		$(":submit").live("mouseout", function() {goDim(this)})
	})
