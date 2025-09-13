function filtrar() {
    var filter, li, txtValue;
    filter = document.getElementById("myInput").value.toUpperCase();
    li = document.getElementsByTagName("li");
    for (var i = 0; i < li.length; i++) {      
      if (li[i].getAttribute("class") != 'title') {
        if (li[i].getAttribute("class") == 'has-children') {
          txtValue = '';
          for (var j = 0; j < li[i].getElementsByTagName('li').length; j++) {
            txtValue = txtValue+' '+ li[i].getElementsByTagName('li')[j].innerHTML + String(li[i].getElementsByTagName('li')[j].getAttribute("group"));
          }
        } else{
          txtValue = li[i].textContent + ' ' + li[i].innerText+' '+ String(li[i].getAttribute("group"));
        }
        if (txtValue.toUpperCase().indexOf(filter) > -1) {
            li[i].style.display = "";
        } else {
            li[i].style.display = "none";
        }
      }
    }
}

$(document).ready(function() {
  document.getElementById('fileinput').onchange = function(){
    var file = this.files[0];
    if (file.name.endsWith('.m3u')) {
      var reader = new FileReader();
      reader.onload = lerArquivo;
      reader.readAsText(file);
      gerarDiv2();
    } else{
      alert('O arquivo deve possuir o formato .m3u');
    }
  }
  $("#drop_zone").click(function(e){
    e.preventDefault();
    $("#fileinput").trigger('click');
  });  

});

function transferirLi(item){
  var id;
  var mainTo = item.closest('div').attr('id') == 'div1' ? '2':'1';  
  id = item.closest('.has-children').attr('id');
  order = item.closest('.has-children').attr('order');
  if ($('#Grupo'+mainTo).find('#'+id).length > 0) {
    $('#Grupo'+mainTo).find('#'+id+' ul').append(item);
  }else{
    var grupo = item.closest('.has-children').find('label').html();
    var div = document.getElementById('Grupo'+mainTo);
    div.appendChild(createLiGrupo(grupo,id));
    $('#Grupo'+mainTo).find('#'+id+' ul').append(item);
  }
  if ($('#Grupo'+(mainTo == '1'?'2':'1')).find('#'+id+' ul li').length == 0) {
    $('#Grupo'+(mainTo == '1'?'2':'1')).find('#'+id).remove();
  }
}
function createTitulo(id){
  var liTitulo = document.createElement("li");
  liTitulo.innerHTML = "Lista "+id;
  liTitulo.className = "title";
  var button = document.createElement("button");
  button.addEventListener('click',function(e){
    download(id);
  },false);
  liTitulo.appendChild(button);
  liTitulo.setAttribute('draggable',"false");  
  return liTitulo;
}

function gerarDiv2(){
  var div = document.getElementById('div2');
  div.innerHTML = '';
  var body = document.createElement("ul");
  body.id = 'Grupo2';
  body.className = 'cd-accordion-menu';
  body.addEventListener('dragover',allowDrop);
  body.addEventListener('drop',drop);
  body.appendChild(createTitulo(2));
  div.appendChild(body);
}

function gerarDiv3(){
  var div = document.getElementById('div3');
  div.innerHTML = '';
  var body = document.createElement("ul");
  body.id = 'Grupo3';
  body.className = 'cd-accordion-menu';
  body.addEventListener('dragover',allowDrop);
  body.addEventListener('drop',drop);
  body.appendChild(createTitulo(2));
  div.appendChild(body);
}

function createLiGrupo(nome,id){
  var liGrupo = document.createElement("li");
  liGrupo.className = 'has-children';
  liGrupo.setAttribute('draggable','true');
  liGrupo.addEventListener('dragstart',drag);
  liGrupo.addEventListener('contextmenu',function(ev ){
    ev.preventDefault();
    var target = ev.target;
    if (target.tagName == 'LABEL') {
      
      var textInput = document.createElement('input');
      textInput.setAttribute('type','text');
      textInput.setAttribute('value',target.textContent);
      textInput.id = "edicao";
      textInput.className = "textFieldEdit";
      ev.target.parentElement.setAttribute('draggable','false');
      textInput.addEventListener('blur',function(e){
        ev.target.innerHTML = '';
        var li = ev.target.getAttribute('for');
        $('#Grupo2').find('#l'+li).find('label').text(this.value);
        $('#Grupo1').find('#l'+li).find('label').text(this.value);
        var lista = $('#Grupo2').find('#l'+li).find('ul li');
        for (var i = 0; i < lista.length; i++) {
          lista[i].setAttribute('group',this.value);
        }
        var lista = $('#Grupo1').find('#l'+li).find('ul li');
        for (var i = 0; i < lista.length; i++) {
          lista[i].setAttribute('group',this.value);
        }
        ev.target.textContent = this.value;
        ev.target.parentElement.setAttribute('draggable','true');
      });
      ev.target.innerHTML = '';
      ev.target.appendChild(textInput);
      document.getElementById("edicao").focus();
    }
    return false;
  }, false);
  if (parseInt(id) || id == 0) {
    liGrupo.innerHTML = '<input type="checkbox" id="group-'+id+'" class = "inputItem">'; 
    liGrupo.innerHTML += '<label for="group-'+id+'">'+nome+'</label>';
    liGrupo.id = 'lgroup-'+id;
    liGrupo.setAttribute('order',id);
    liGrupo.style.order = id;
  }else{
    var order = id.replace( /^\D+/g, '');
    liGrupo.id = id;
    liGrupo.setAttribute('order',order);
    liGrupo.style.order = order;
    liGrupo.innerHTML = '<input type="checkbox" id="'+id.replace('l','s')+'" class = "inputItem" checked>';
    liGrupo.innerHTML += '<label for="'+id.replace('l','s')+'">'+nome+'</label>';
    liGrupo.innerHTML += '<ul></ul>';
  }
  return liGrupo;
}

function gerarDiv1(sortable,list){
  var grupo = "";
  var div = document.getElementById('div1');
  div.innerHTML = '';
  var body = document.createElement("ul");
  body.addEventListener('dragover',allowDrop);
  body.addEventListener('drop',drop);
  body.className = 'cd-accordion-menu';
  body.id = 'Grupo1';
  body.appendChild(createTitulo(1));
  var ulGrupo = '';
  for (var i = 0; i < sortable.length; i++) {
    if ( sortable[i][1].group !== grupo) {
      grupo = sortable[i][1].group;
      var liGrupo = createLiGrupo(grupo,i);
      var ul = document.createElement("ul");
      let itens = list.filter(item =>{
        return item.group == grupo;
      });
      for (var j = 0; j < itens.length; j++) {
        var li = document.createElement("li");
        item = itens[j];
        li.innerHTML = item.name;
        li.className = 'item'+j;
        li.style.order = j;
        li.setAttribute('link',item.link);
        li.id = (item.id.length == 0) ? "" : item.id;
        li.setAttribute('name',item.name);
        li.setAttribute('logo',item.logo);
        li.setAttribute('channel',item.channel);
        li.setAttribute('group',grupo);
        ul.appendChild(li);
      }
      liGrupo.appendChild(ul);
      body.appendChild(liGrupo);
    }
  }
  div.appendChild(body);
  var x = $('#div1').height();
  $('.cd-accordion-menu').css('min-height', x);
  $('.cd-accordion-menu').css('min-height', x);
}


function download(id) {
  var element = document.createElement('a');
  var lista = document.getElementById("Grupo"+id).getElementsByTagName("li");
  var text = '#EXTM3U \n';
  for (var i = 0; i < lista.length; i++) {
    if (lista[i].className != 'has-children' && lista[i].className !='title') {
      id = lista[i].getAttribute("id");
      name = lista[i].getAttribute("name");
      logo = lista[i].getAttribute("logo");
      group = lista[i].getAttribute("group");
      channel = lista[i].getAttribute("channel");
      link = lista[i].getAttribute("link");
      text = text+'#EXTINF:-1 tvg-id="'+id+'" tvg-name="'+name+'" tvg-logo="'+logo+'" group-title="'+group+'",'+channel+'\n'+link+'\n';
    }
  }
  element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
  element.setAttribute('download', 'arquivo.m3u');
  element.style.display = 'none';
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
}

function drag(ev) {
  ev.dataTransfer.setData("text", ev.target.id);
  ev.dataTransfer.setData("grupo", ev.target.parentElement.id);
}

function drop(ev) {
  ev.preventDefault();
  var data = ev.dataTransfer.getData("text");
  var grupo = ev.dataTransfer.getData("grupo");
  var target = ev.target;
  while(target.className != 'cd-accordion-menu'){ 
    target = target.parentElement;
  }
  if (target.id != grupo) {
    var list = $('#'+target.id).find(' #'+data);
    if (list.length > 0) {
      var list2 = $('#'+target.id).find(' #'+data+' ul li');
      $('#'+((target.id)=='Grupo1'?'Grupo2':'Grupo1')).find(' #'+data+' ul').append(list2);
      $('#'+target.id).find(' #'+data).remove();
      $('#'+target.id).append($('#'+((target.id)=='Grupo1'?'Grupo2':'Grupo1')).find(' #'+data));
    } else {
      target.appendChild(document.getElementById(data));
    }
  }
}


function allowDrop(ev) {
  ev.preventDefault();
}

function dropHandler(ev) {

  // Prevent default behavior (Prevent file from being opened)
  ev.preventDefault();

  if (ev.dataTransfer.items) {
    // Use DataTransferItemList interface to access the file(s)
    for (var i = 0; i < ev.dataTransfer.items.length; i++) {
      // If dropped items aren't files, reject them
      if (ev.dataTransfer.items[i].kind === 'file') {
        var file = ev.dataTransfer.items[i].getAsFile();
        if (file.name.endsWith('.m3u')) {
          
          /*console.log('... file[' + i + '].name = ' + file.name);*/
          var reader = new FileReader();
          reader.onload = lerArquivo;
          reader.readAsText(file);
          gerarDiv2();
        } else{
          alert('O arquivo deve possuir o formato .m3u');
        }
      }
    }
  }
}
function dragOverHandler(ev) {
  ev.preventDefault();
}

function lerArquivo(progressEvent){
  var lines = this.result.split('\n');
  var list = [];
  $(".drop_zone").hide();
  document.querySelector('#fileinput').required = false;
  for(var line = 0; line < lines.length; line++){

    var text = lines[line];
    if (text.includes("#EXTINF")) {

      var ind = text.lastIndexOf("tvg-id");
      var id = text.substring(ind,text.indexOf("\" ",ind+1)).replace('tvg-id="', "");

      var ind = text.lastIndexOf("tvg-name");
      var name = text.substring(ind,text.indexOf("\" ",ind+1)).replace('tvg-name="', "");

      var ind = text.lastIndexOf("tvg-logo");
      var logo = text.substring(ind,text.indexOf("\" ",ind+1)).replace('tvg-logo="', "");

      var ind = text.lastIndexOf("group-title");
      var group = text.substring(ind,text.indexOf("\",",ind+1)).replace('group-title="', "");
      if (group.length == 0) {
        group = '- Sem grupo'
      }
      var ind = text.lastIndexOf(",");
      var channel = text.substring(ind,ind+99).replace(',', "");          

      list.push({group:group,name:name,logo:logo,id:id,channel:channel,link:lines[line+1]});
    }
  }
  var sortable = [];
  for (var item in list) {
    
    sortable.push([item, list[item]]);
  }
  sortable.sort(function(a, b) {
      var nameA= a[1].group.toLowerCase(), nameB= b[1].group.toLowerCase()
      if (nameA < nameB) 
          return -1 
      if (nameA > nameB)
          return 1
      return 0 
  });
  gerarDiv1(sortable,list);
  $( ".has-children li" ).click(function() {
    transferirLi($(this));
  });
};
