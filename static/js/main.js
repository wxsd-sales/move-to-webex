
var selectAll = {'main':false, 'pmi':false}
var meetingData = null;
var meetingDataPMI = null;

function fadeInSearchDescription(){
  $('#searchDescription').fadeIn(500, finalizeSearchComplete);
}

function finalizeSearchComplete(){
  $('#searchMeetingsDiv').removeClass('high-div');
  $('#searchMeetingsDiv').addClass('default-height-div');
}

function fadeInSearchSuccessImg(){
  $('#searchCompleteImg').fadeIn();
}

function fadeInTransferCompleteImg(){
  $('#transferCompleteImg').fadeIn();
}

let calendar = null;
function showOverlay(){
  $('#overlay').show();
}

function closeOverlay(){
  $('#overlay').hide();
  if(calendar != null){
    calendar.destroy();
  }
  $('#form-content').find("*").off();//disable all of the field event listeners whenever the overlay form is closed. -  otherwise they'll stack.
}

function completeTransferBox(){
  return '<i class="icon icon-check-circle_16" style="color:green"></i>';
}

function buildTable(key, columns, tbody){
  let table = $('<table class="table table-sm table-striped table-hover table-custom table-responsive">');

  let tr = $('<tr>').append(
            $('<th scope="col">').append(
              $('<i class="icon icon-check-circle_16"></i>').on('click', function(e){
                if(!selectAll[key]){
                  selectAll[key] = true;
                  $('.custom-checkbox').prop('checked', true);
                } else {
                  selectAll[key] = false;
                  $('.custom-checkbox').prop('checked', false);
                }
              })
            )
          );

  for(column of columns){
    tr.append($('<th scope="col">').text(column));
  }

  table.append($('<thead>').append(tr), tbody);
  return table;
}

function rowOnClick(meeting, meetingRow, source){
  if(!meeting.hasOwnProperty('webex_meeting_id')){
    meetingRow.on('click', function(e){
      console.log(source);
      console.log(e.currentTarget.id);
      console.log($(e.currentTarget));
      let myid = e.currentTarget.id.replace("row_","");
      let selectedData = null;
      if(source == "pmi"){
        selectedData = getPMIMeeting(myid);
      } else {
        selectedData = meetingData[myid];
      }

      console.log(`selectedData:${selectedData}`);
      $("#setMeetingId").text(myid);

      $('#setTopic').val(selectedData["topic"]).on('input', function(e){
          selectedData["topic"] = $(this).val();
          $("#topic_"+myid).text($(this).val());
      });

      $('#setParticipants').val(selectedData["attendees"]).on('input', function(e){
          selectedData["attendees"] = $(this).val().split(',');
          $("#attendees_"+myid).text($(this).val());
      });

      $("#durationSelect").val(selectedData["duration"]).on('change', function(e){
          selectedData["duration"] = parseInt($(this).val());
          $("#duration_"+myid).text($(this).val());
      });

      let startTimeSelector = $(e.currentTarget).find("#start_time");
      defaultDateStr = selectedData["start_time"];
      console.log(defaultDateStr);
      if(new Date(defaultDateStr) < new Date()){
        $('#setStartTime').val("MEETING DATE IN THE PAST");
      } else if (defaultDateStr == undefined){
        $('#setStartTime').val("INVALID DATE");
      }
      if(e.target.name != "checkbox"){
        calendar = $('#setStartTime').flatpickr({
          enableTime: true,
          dateFormat: "Y-m-d H:i",
          defaultDate: selectedData["start_time"],
          minDate: "today",
          time_24hr: false,
          onChange: function(selectedDates, dateStr, instance) {
            console.log('on change func!')
            let newDateString = selectedDates[0].toISOString();
            selectedData["start_time"] = newDateString;
            setDisplayDate(startTimeSelector, newDateString);
          },
        });
        showOverlay();
      }
    });//end meetingRow.on click
  }
}

function setDisplayDate(selector, startTime){
  return selector.text(new Date(startTime).toLocaleString());
}

function getPMIMeeting(meetingId){
  for(let m of meetingDataPMI["meetings"]){
    if(m["msft_id"] == meetingId){
      return m;
    }
  }
}


function buildPMITBody(pmiMeetings){
  let tbody = $('<tbody>');
  for(let meeting of pmiMeetings['meetings']){
    let meetingRow = makeRow(pmiMeetings['id'], meeting, "pmi");
    rowOnClick(meeting, meetingRow, 'pmi');
    tbody.append(meetingRow);
  }
  return tbody;
}

function buildTBody(meetingData){
  let tbody = $('<tbody>');
  for(let i of Object.keys(meetingData)){
    let meetingRow = makeRow(i, meetingData[i], "main");
    rowOnClick(meetingData[i], meetingRow, 'main')
    tbody.append(meetingRow);
  }
  return tbody;
}


function setCheckbox(id, meetingDataCell){
  let webexMeetingId = "";
  let checkboxHTML = '<input type="checkbox" class="custom-checkbox" name="checkbox" id="'+id+'"></input>';
  if(meetingDataCell.hasOwnProperty('webex_meeting_id')){
    webexMeetingId = meetingDataCell['webex_meeting_id'];
    checkboxHTML = completeTransferBox();
  }
  return {'html': checkboxHTML, 'webexId':webexMeetingId};
}

function capitalizeFirstLetter(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

const recurTypes = {"daily":"day", "weekly": "week", "relativeMonthly":"week", "absoluteMonthly":"month", "yearly":"year"}
function setRecurrenceString(recurrenceJson, startTime){
  if(recurrenceJson == null){
    return "";
  } else {
    let returnStr = "Every ";
    let recurType = recurTypes[recurrenceJson['pattern']['type']];
    let interval = recurrenceJson['pattern']['interval'];
    if(recurrenceJson['pattern']['type'] == "relativeMonthly"){
      returnStr += interval == 1 ? `month ` : `${interval} months `;
      returnStr += "on the " + recurrenceJson['pattern']['index'] + " ";
    } else {
      if(recurType == 'day' && interval == 1){
        returnStr += 'day ';
      } else if(interval == 1){
        returnStr += `${recurType} on `
      } else {
        returnStr += `${interval} ${recurType}s on `;
      }
    }

    let frequencyString = "";
    if(recurType == "week"){
      for(let day of recurrenceJson['pattern']['daysOfWeek']){
        day = capitalizeFirstLetter(day);
        if(frequencyString.length == 0){
          frequencyString = `${day}`;
        } else {
          frequencyString += `, ${day}`;
        }
      }
    } else if(recurType == "month"){
      let day = recurrenceJson['pattern']['dayOfMonth']
      frequencyString = `the ${day}`;
      if(parseInt(day) == 1){
        frequencyString += "st";
      } else if(parseInt(day) == 2){
        frequencyString += "nd";
      } else if(parseInt(day) == 3){
        frequencyString += "rd";
      } else {
        frequencyString += "th";
      }
    }
    if(frequencyString.length > 0){
      returnStr += `${frequencyString} `;
    }

    if(recurrenceJson['range']['type'] == "noEnd"){
      returnStr += 'until cancelled.';
    } else if (recurrenceJson['range']['type'] == "endDate"){
      returnStr += `until ${recurrenceJson['range']['endDate']}.`;
    } else {
      returnStr += "until: " + JSON.stringify(recurrenceJson['range']);
    }

    startDate = new Date(startTime);
    now = new Date();
    let returnDate = null;
    if(startDate != "Invalid Date" && startDate < now){
      now.setHours(startDate.getHours());
      now.setMinutes(startDate.getMinutes());
      now.setSeconds(startDate.getSeconds());
      if(now < new Date()){//did setting the time above end us up in the past?
        now.setDate(now.getDate() + 1);
      }
      if(recurType == "day"){
        returnDate = now;
      } else if(recurType == "week"){
        let daysOfWeek = recurrenceJson['pattern']['daysOfWeek'];
        if(daysOfWeek.length > 0){
          attempts = 0
          weekdays = {0:"sunday", 1:"monday", 2:"tuesday", 3:"wednesday", 4:"thursday", 5:"friday", 6:"saturday"}
          weekday = weekdays[now.getDay()];
          while(daysOfWeek.indexOf(weekday) < 0 && attempts < 7){
            now.setDate(now.getDate() + 1);
            weekday = weekdays[now.getDay()];
            attempts += 1;
          }
          if(attempts < 8){
            returnDate = now;
          }
        }
      } else if(recurType == "month"){
        now.setDate(startDate.getDate());
        if(now < new Date()){
          now.setMonth(now.getMonth() + 1);
        }
        returnDate = now;
      }
    }
    return {"string":returnStr, "date":returnDate};
  }
}

function makeRow(id, meeting, source){
  let cell_id = id;
  if(source == "pmi"){ cell_id = meeting["msft_id"]; }
  let checkbox = setCheckbox(cell_id, meeting);
  let recurrence = setRecurrenceString(meeting['recurrence_msft'], meeting["start_time"]);
  let startDate = meeting["start_time"];
  if([undefined, null].indexOf(recurrence["date"]) < 0){
    startDate = recurrence["date"];
    meeting["start_time"] = recurrence["date"].toISOString().split(".")[0] + "Z"
  }

  let participants = "";
  if(meeting.hasOwnProperty('attendees')){
    participants = meeting['attendees'];
  }

  let row = $('<tr id="row_'+cell_id+'">');
  row.append($('<th id="checkbox_html_'+cell_id+'"scope="row">').html(checkbox['html']))
  if(pageVersion == null){
    row.append($('<td>').text(id));
  }
  let subject = meeting['topic'];
  if(subject == undefined){
    subject = meeting['subjects'][0];
  }

  let duration = meeting['duration'];
  if(duration == undefined){
    duration = meeting['duration_msft'];
  }
  row.append($('<td id="topic_'+cell_id+'" class="scroll-cell">').text(subject),
             $('<td id="webex_id_'+cell_id+'">').text(checkbox['webexId']),
             setDisplayDate($('<td id="start_time">'), startDate),
             $('<td id="duration_'+cell_id+'">').text(duration),
             $('<td>').text(recurrence["string"]),
             $('<td id="attendees_'+cell_id+'" class="scroll-cell">').text(participants),
           );
  return row;
}

function displayData(){
  $('#transferMeetingsDiv').remove();
  $("#searchResults").show();
  console.log(meetingData);

  if(meetingData.hasOwnProperty('pmi')){
    meetingDataPMI = meetingData['pmi'];
    delete meetingData['pmi'];
  }

  let tbody = buildTBody(meetingData);

  let columns = ["Subject", "Webex MeetingId", "StartTime", "Duration", "Recurrence", "Participants"];
  if(pageVersion == null){
    columns.splice(0, 0, "Zoom MeetingId")// .splice(insertAtIndex, deleteXItems (0), Value)
  }
  
  let table = buildTable('main', columns, tbody);

  let mainLabel = $('<label>').text(`${meetingTypeTitle}Meetings:`);
  $('#searchResults').append(
    mainLabel,
    $('<div class="meetings-table">').append(table)
  )
  console.log(meetingDataPMI);
  if(meetingDataPMI.hasOwnProperty('meetings') && meetingDataPMI['meetings'].length > 0){
    let pmiTBody = buildPMITBody(meetingDataPMI);
    let pmiColumns = ["PMI", "Subject", "Webex MeetingId", "StartTime", "Duration", "Recurrence", "Participants"];
    let pmiTable = buildTable('pmi', pmiColumns, pmiTBody);
    let msftLabel = $('<label>').text("The following PMI meetings were found in Microsoft Calendar, but not your Zoom account:");
    $('#searchResults').append(
      msftLabel,
      $('<div class="meetings-table">').append(pmiTable)
    );
  }
  $('#transferNextStepImg').fadeIn();
  addTransferButton('#searchResults', ` my selected ${meetingTypeTitle}meetings to Webex.`);
  //$('#transferNextStepImg').fadeOut(500, fadeInTransferCompleteImg);
}

function addTransferButton(selector, text){
  $(selector).append(
    $('<div class="transfer-spinner spinner-border blue-font" style="display:none;"></div>'),
    $('<button id="transferButton" type="button" class="btn btn-primary">Transfer</button>').on('click', function(e){
      if($('#searchWarningText').length){
        $('#searchWarningText').remove();
      }
      let checkedBoxes = $('.custom-checkbox:checkbox:checked');
      if(checkedBoxes.length == 0){
        let warningText = $('<div id="searchWarningText" class="warning-text alert-danger" role="alert">').text('You must select 1 or more meetings to transfer.')
        $('#searchResults').append(warningText);
      } else {
        $('#transferButton').hide();
        $('#transferDescriptionText').hide();
        $('.transfer-spinner').show();
        meetings = {}
        for(let box of checkedBoxes){
          if(meetingData[box.id] == undefined){
            meetings[box.id] = getPMIMeeting(box.id);
          } else {
            meetings[box.id] = meetingData[box.id];
          }
        }
        console.log(meetings);
        data = {"command":"transfer", "meetings":meetings};
        $.post('/command', JSON.stringify(data), function(resp){
          console.log('/command transfer response:');
          console.log(resp);
          let jresp = JSON.parse(resp);
          $('.transfer-spinner').hide();
          $('#transferButton').show();
          $('#transferDescriptionText').show();
          if(jresp['code'] == 200){
            $('#transferNextStepImg').fadeOut(500, fadeInSearchSuccessImg);
            let returnData = jresp['data'];
            for(let id of Object.keys(returnData)){
              if(typeof(returnData[id]) == "string"){
                $('#webex_id_'+id).text(returnData[id]);
                $('#webex_id_'+id).removeClass('red-font');
                $('#checkbox_html_'+id).html(completeTransferBox());
                $('#row_'+id).off('click');
              } else {//else, returnData[id] isn't a string, then it's an error object
                $('#webex_id_'+id).text(returnData[id]["error_reason"]);
                $('#webex_id_'+id).addClass('red-font');
              }
            }
          } else {
            console.log(jresp);
            if(jresp["code"] == 401){
              window.location = '/webex-oauth';
            }
          }
        })
      }
    }),
    $('<p id="transferDescriptionText" class="div-description">'+text+'</p>')
  );
}

function setDivSuccess(selector){
  $(selector).removeClass('alert-primary');
  $(selector).addClass('alert-success');
  $(selector).removeClass('enable-cursor');
  $(selector).addClass('default-cursor');
}

function setDivReady(selector, cursor){
  $(selector).removeClass('alert-secondary');
  $(selector).addClass('alert-primary');
  $(selector).removeClass('disable-cursor');
  if(cursor !== false){
    $(selector).addClass('enable-cursor');
  }
}

function searchFunction(){
  let searchTerm = null;
  if(pageVersion == "simplified"){
    $('#searchInput').hide();
    searchTerm = $('#searchInput').val();
  }
  if(!searching){
    searching = true;
    $('#searchButton').fadeOut();
    $('#searchDescription').fadeOut();
    $('.search-spinner').fadeIn();
    data = {"command":"search", "version":pageVersion, "search_term":searchTerm};
    $.post('/command', JSON.stringify(data), function(resp){
      console.log('/command search response:');
      let jresp = JSON.parse(resp);
      if(jresp['code'] == 200){
        let meetingIds = Object.keys(jresp['data']);
        let numMeetings = meetingIds.length;
        var index = meetingIds.indexOf('pmi');
        if (index !== -1) {
          numMeetings -= 1
          if(jresp['data']['pmi'].hasOwnProperty('meetings')){
            numMeetings += jresp['data']['pmi']['meetings'].length;
          }
        }
        $('#searchDescription').html("Found " + numMeetings +` ${meetingTypeTitle}meetings.`);
        $('.search-spinner').fadeOut(500, fadeInSearchDescription);
        $('#searchNextStepImg').fadeOut(500, fadeInSearchSuccessImg);
        setDivSuccess('#searchMeetingsDiv');
        meetingData = jresp['data'];
        displayData();
      } else {
        console.log(jresp);
        if(jresp["code"] == 401){
          window.location = '/webex-oauth';
        }
      }
    })
  }
}

function msftConfig(){
  if(msftToken != "None"){
    $('#searchNextStepImg').show();
    $('#searchButton').prop('disabled', false);
    if(pageVersion == 'simplified'){
      setDivReady('#searchMeetingsDiv', false);
      $('#searchButton').on('click', function(){
        let searchInput = $('#searchInput').val();
        if(searchInput.length == 0){
          $("#searchError").show();
        } else {
          $("#searchError").hide();
          searchFunction();
        }
      });
    } else {
      setDivReady('#searchMeetingsDiv');
      $('#searchMeetingsDiv').on('click', searchFunction);
    }
    
  } else {
    setDivReady('#msftSignInDiv');
    $('#msftNextStepImg').show();

    $('#msftSignInButton').prop('disabled', false);
    $('#msftSignInDiv').on('click', function(){
      let winLoc = '/azure';
      if(pageVersion != null){
        winLoc = `/azure?state=${pageVersion}`
      }
      window.location = winLoc;
    })
  }
}


$('document').ready(function() {
  $('#webexAvatar').attr('src', webexAvatar);
  addTransferButton('#transferMeetingsDiv', ` my ${meetingTypeTitle}meetings to Webex.`);

  $('#searchButton').prop('disabled', true);
  $('#transferButton').prop('disabled', true);


  if(msftToken != "None"){
    setDivSuccess('#msftSignInDiv');
    $('#msftSignInDiv').html('Successfully Signed in to Microsoft Outlook!');
    $('#msftSignInDiv').removeClass('disable-cursor');
    $('#msftCompleteImg').show();
    $('#msftNextStepImg').hide();
  } else {
    $('#msftSignInButton').prop('disabled', true);
  }

  if(zoomToken != "None"){ //if user is signed into Zoom.
    setDivSuccess('#zoomSignInDiv');
    $('#zoomSignInDiv').html('Successfully Signed in to Zoom!');
    $('#zoomCompleteImg').show();
    $('#zoomNextStepImg').hide();

    msftConfig();

  } else { // else, user is not signed into Zoom.

    if(pageVersion == null){
      $('#zoomSignInDiv').on('click', function(){
        window.location = '/zoom-oauth';
      })
    } else if(pageVersion == 'simplified'){
      msftConfig();
    }

  }

  $("#overlay").on('click', function(e){
    if(e.target.id == "overlay"){
      closeOverlay()
    }
  })

  $("#close-form").on('click', function(e){
    closeOverlay()
  })

  if(!isNaN(meetingsCount)){
    $("#zoomMeetingsDescription").text(" my " + meetingsCount + ` ${meetingTypeTitle}meetings to Webex.`);
  }


})
