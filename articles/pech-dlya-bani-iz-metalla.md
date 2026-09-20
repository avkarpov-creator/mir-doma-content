---
title: "Печь для бани своими руками из металла: конструкция и сборка"
slug: "pech-dlya-bani-iz-metalla"
seo_title: "Печь для бани своими руками из металла: сборка"
seo_description: "Печь для бани своими руками из металла: конструкция топки и каменки, какой металл брать, расчёт камней по объёму парной. Сборка пошагово и ошибки."
focus_keyword: "печь для бани своими руками из металла"
category: "Баня и сауна"
tags:
  - банная печь
  - баня
status: draft
images:
  - images/pech-dlya-bani-iz-metalla.jpg
  - images/pech-dlya-bani-iz-metalla-2.jpg
  - images/pech-dlya-bani-iz-metalla-3.jpg
  - images/pech-dlya-bani-iz-metalla-4.jpg
  - images/pech-dlya-bani-iz-metalla-5.jpg
  - images/pech-dlya-bani-iz-metalla-6.jpg
---

# Печь для бани своими руками из металла: конструкция и сборка

Банная печь-каменка — не то же самое, что печь для отопления дома: ей нужно
держать камни для пара, безопасно работать в условиях высокой влажности и
при этом быстро прогревать небольшой объём парной. Сварить такую печь из
трубы или листового металла своими руками дешевле, чем купить готовую, если
есть навык сварки и понимание конструкции. Разберём саму конструкцию,
какой металл брать и как посчитать камни под объём парной.

![Самодельная металлическая печь для бани с баком для камней](images/pech-dlya-bani-iz-metalla.jpg)

## Из чего состоит банная печь

- **Топка** — камера сгорания дров, обычно из трубы диаметром 400–500 мм
  или согнутого листового металла.
- **Зольник** — нижний отсек под колосниковой решёткой, куда падает зола;
  через его дверцу же регулируется подача воздуха на горение.
- **Каменка** — бак или решётка для камней над топкой. Открытая каменка —
  камни лежат открыто сверху, воздух прогревается быстро, пар мягкий.
  Закрытая — камни в отдельном кожухе с дверцей, пар получается плотным
  и сухим при плескании воды через дверцу, жар держится дольше после
  протопки.
- **Дымоход** — патрубок и труба для отвода дыма, с разделкой через
  кровлю или стену с соблюдением пожарных отступов.
- **Бак для воды (опционально)** — встроенный сбоку от топки или выносной,
  подключённый трубкой к теплообменнику в стенке топки.

## Какой металл брать

- **Топка и корпус** — сталь от 4–6 мм. Тоньше 3 мм прогорает за один-два
  сезона активной топки, особенно в зоне прямого контакта с пламенем.
- **Каменка (кожух под камни)** — жаропрочная сталь тех же толщин, не
  оцинкованная сталь: цинковое покрытие при сильном нагреве выделяет пары,
  опасные для дыхания в закрытом помещении парной.
- **Бак для воды** — нержавеющая сталь, если бак встроенный и контактирует
  с топочными газами через теплообменник — обычная сталь там быстро
  корродирует от постоянного контакта с горячей водой и паром.
- **Дымоход** — сталь с термостойким покрытием или нержавейка, обычный
  чёрный металл на дымоходе прогорает от постоянного конденсата и высоких
  температур отходящих газов.

![Труба и лист металла для сборки корпуса печи и топки](images/pech-dlya-bani-iz-metalla-2.jpg)

## Расчёт камней по объёму парной

### Калькулятор массы камней

<!-- wp:html -->
<div id="mdPbCalc" class="md-pb">
<div class="md-pb__head">
<h3 class="md-pb__title">Калькулятор массы камней для каменки</h3>
<p class="md-pb__sub">Считает объём парной и рекомендуемую массу камней по типу каменки.</p>
</div>
<div class="md-pb__grid">
<label class="md-pb__f"><span>Площадь парной, м²</span><input type="number" id="pbArea" value="6" min="1" max="40" step="0.5"></label>
<label class="md-pb__f"><span>Высота потолка, м</span><input type="number" id="pbHeight" value="2.2" min="1.8" max="3" step="0.05"></label>
<label class="md-pb__f"><span>Тип каменки</span>
<select id="pbType">
<option value="20">Открытая — 20 кг на 1 м³</option>
<option value="30" selected>Закрытая — 30 кг на 1 м³</option>
</select></label>
</div>
<div class="md-pb__res">
<div class="md-pb__resitem"><span>Объём парной</span><b id="pbVolume">13,2 м³</b></div>
<div class="md-pb__resitem"><span>Масса камней</span><b id="pbStones">396 кг</b></div>
</div>
<p class="md-pb__note">Расчёт ориентировочный, по общепринятому правилу кг камней на м³ парной. Точный объём каменки уточняйте по паспорту конкретной топки.</p>
<div class="md-pb__actions">
<button type="button" id="pbCopy" class="md-pb__btn md-pb__btn--main">Скопировать результат</button>
<a id="pbVk" class="md-pb__btn md-pb__btn--vk" href="#" target="_blank" rel="noopener noreferrer">Поделиться ВКонтакте</a>
<a id="pbTg" class="md-pb__btn md-pb__btn--tg" href="#" target="_blank" rel="noopener noreferrer">Поделиться в Telegram</a>
<button type="button" id="pbShareNative" class="md-pb__btn" hidden>Поделиться…</button>
<button type="button" id="pbPrint" class="md-pb__btn">Печать</button>
</div>
<p id="pbStatus" class="md-pb__status"></p>
</div>
<style>
.md-pb{--pb-g:#3d7a3d;--pb-bd:#e2e2e2;--pb-bg:#f7faf7;--pb-vk:#0077ff;--pb-tg:#26a5e4;max-width:760px;margin:28px auto;padding:20px;border:1px solid var(--pb-bd);border-radius:14px;background:#fff;font-family:inherit;color:#222;line-height:1.5;box-sizing:border-box}
.md-pb *{box-sizing:border-box}
.md-pb__title{margin:0 0 6px;font-size:1.3em;color:var(--pb-g)}
.md-pb__sub{margin:0 0 16px;font-size:.9em;color:#666}
.md-pb__grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin-bottom:16px}
.md-pb__f{display:flex;flex-direction:column;gap:5px;font-size:.88em;font-weight:600;color:#444}
.md-pb__f input,.md-pb__f select{padding:10px 12px;border:1px solid var(--pb-bd);border-radius:9px;font-size:16px;font-family:inherit;font-weight:400;background:#fafafa;width:100%}
.md-pb__f input:focus,.md-pb__f select:focus{outline:none;border-color:var(--pb-g);background:#fff}
.md-pb__res{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;padding:14px;background:var(--pb-bg);border-radius:10px;margin-bottom:10px}
.md-pb__resitem{text-align:center}
.md-pb__resitem span{display:block;font-size:.8em;color:#666;margin-bottom:3px}
.md-pb__resitem b{font-size:1.15em;color:var(--pb-g)}
.md-pb__note{margin:0 0 6px;font-size:.83em;color:#888;font-style:italic}
.md-pb__actions{display:flex;gap:9px;margin-top:10px;flex-wrap:wrap}
.md-pb__btn{flex:1 1 auto;min-width:130px;padding:12px 16px;border:1px solid var(--pb-g);border-radius:9px;background:#fff;color:var(--pb-g);font-size:.95em;font-family:inherit;font-weight:600;cursor:pointer;text-align:center;text-decoration:none;display:inline-block}
.md-pb__btn--main{background:var(--pb-g);color:#fff}
.md-pb__btn--vk{border-color:var(--pb-vk);color:var(--pb-vk)}
.md-pb__btn--tg{border-color:var(--pb-tg);color:var(--pb-tg)}
.md-pb__btn:active{opacity:.7}
.md-pb__status{margin:10px 0 0;font-size:.87em;color:var(--pb-g);min-height:1.2em;text-align:center}
@media (max-width:600px){.md-pb{padding:15px;border-radius:11px}.md-pb__grid{grid-template-columns:1fr}}
@media print{.md-pb__actions,.md-pb__status,.md-pb__sub{display:none}.md-pb{border:none;max-width:100%}}
</style>
<script>
(function(){
var $=function(id){return document.getElementById(id)};
function nf(x,d){d=(d===undefined)?1:d;return x.toFixed(d).replace('.',',')}
function calc(){
 var area=parseFloat($('pbArea').value)||0, height=parseFloat($('pbHeight').value)||0;
 var volume=area*height;
 var coef=parseFloat($('pbType').value)||30;
 var stones=volume*coef;
 $('pbVolume').textContent=nf(volume)+' м³';
 $('pbStones').textContent=Math.round(stones)+' кг';
 return {volume:volume,stones:stones};
}
function shortText(){
 var d=calc();
 var t='Парная '+nf(d.volume)+' м³ — камней нужно '+Math.round(d.stones)+' кг';
 t+='. Расчёт: mir-doma.pro/pech-dlya-bani-iz-metalla/';
 return t;
}
function report(){
 var d=calc();
 var t='РАСЧЁТ КАМНЕЙ ДЛЯ КАМЕНКИ\n';
 t+='Объём парной: '+nf(d.volume)+' м³\n';
 t+='Масса камней: '+Math.round(d.stones)+' кг\n';
 t+='\nИсточник: mir-doma.pro/pech-dlya-bani-iz-metalla/';
 return t;
}
function updateShareLinks(){
 var url=location.href.split('#')[0];
 var text=shortText();
 $('pbVk').href='https://vk.com/share.php?url='+encodeURIComponent(url)+'&title='+encodeURIComponent('Расчёт камней для банной печи')+'&description='+encodeURIComponent(text);
 $('pbTg').href='https://t.me/share/url?url='+encodeURIComponent(url)+'&text='+encodeURIComponent(text);
}
function recalc(){ calc(); updateShareLinks(); }
['pbArea','pbHeight','pbType'].forEach(function(id){
 var el=$(id); el.addEventListener('input',recalc); el.addEventListener('change',recalc);
});
function flash(msg){$('pbStatus').textContent=msg;setTimeout(function(){$('pbStatus').textContent='';},2600);}
$('pbCopy').addEventListener('click',function(){
 var t=report();
 function done(){flash('Результат скопирован');}
 if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(done,function(){fb(t,done)});}else fb(t,done);
});
function fb(t,cb){var ta=document.createElement('textarea');ta.value=t;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();try{document.execCommand('copy');cb();}catch(e){}document.body.removeChild(ta);}
if(navigator.share){
 $('pbShareNative').hidden=false;
 $('pbShareNative').addEventListener('click',function(){
  navigator.share({title:'Расчёт камней для банной печи',text:shortText(),url:location.href.split('#')[0]}).catch(function(){});
 });
}
$('pbPrint').addEventListener('click',function(){window.print();});
recalc();
})();
</script>
<!-- /wp:html -->

![Загрузка камней в закрытую каменку банной печи](images/pech-dlya-bani-iz-metalla-3.jpg)

## Сборка печи пошагово

1. Вырезать и приварить дно топки, оставив проём под зольниковую дверцу.
2. Установить колосниковую решётку между топкой и зольником — она должна
   выниматься для чистки золы и замены при прогорании.
3. Приварить дверцы топки и зольника с плотным прилеганием — щели снижают
   контроль тяги и повышают риск угара.
4. Сварить и закрепить кожух каменки над топкой — для закрытой каменки
   предусмотреть дверцу для плескания воды на камни и отверстия для
   выхода пара.
5. Приварить патрубок дымохода в верхней части каменки или сбоку, в
   зависимости от выбранной схемы движения дымовых газов.
6. При необходимости вварить теплообменник под бак для воды — трубу или
   регистр в стенке топки, контактирующую с самым горячим участком
   пламени.
7. Проверить швы на герметичность первой протопкой на улице, до установки
   печи в парную — угар через непроваренный шов в закрытом помещении
   опасен.

## Требования пожарной безопасности

Отступ от печи до горючих стен и мебели — не менее 50 см без защитного
экрана и от 30 см с экраном из негорючего материала. Пол под печью и
разделка дымохода через кровлю или стену — по тем же принципам, что и для
печи отопления дома, с той же разбивкой на противопожарные отступы и
изоляцию: подробно разобрано в статье [печь для
дачи](https://mir-doma.pro/pech-dlya-dachi/), хотя сами конструкции
печей разные.

![Установленная банная печь с соблюдением отступов от стен](images/pech-dlya-bani-iz-metalla-4.jpg)

## Частые ошибки

- **Металл тоньше 4 мм на топку.** Прогорает уже через один-два сезона
  активной эксплуатации, особенно в зоне контакта с открытым пламенем.
- **Оцинкованная сталь на кожухе каменки.** При сильном нагреве цинковое
  покрытие выделяет вредные пары — опасно в закрытом помещении парной.
- **Топка слишком большого объёма под маленькую парную.** Перегревает
  помещение и пережигает дрова впустую — размер топки подбирают под
  реальный объём парной, а не по принципу «больше — лучше».
- **Отсутствие зольника и колосниковой решётки.** Без них горение
  неполное, тяга нестабильная, а зола скапливается прямо в топке.
- **Случайный камень вместо проверенной породы.** Расчёт массы камней
  выше не работает, если засыпать каменку случайным колотым булыжником —
  он трескается в разы быстрее, разбор пород и на что смотреть при выборе —
  в статье [какие камни для банной печи](https://mir-doma.pro/kakie-kamni-dlya-bannoy-pechi/).

## Частые вопросы

### Чем банная печь отличается от печи для дома

Банная печь-каменка держит камни и создаёт пар, рассчитана на быстрый
разогрев небольшого влажного помещения. Печь для дома работает на
равномерный долгий обогрев сухого жилого пространства без функции пара.

### Какой толщины металл нужен для печи бани

От 4 мм для стенок топки, тоньше 3 мм прогорает за один-два сезона
активной топки. Кожух каменки — та же толщина, жаропрочная сталь без
оцинковки.

### Открытая или закрытая каменка лучше для бани

Закрытая держит жар дольше и даёт более сухой плотный пар при поливе воды
через дверцу — популярнее для классической русской бани. Открытая быстрее
прогревает воздух в парной, но пар мягче и не такой стойкий.

### Сколько камней нужно на банную печь

Ориентировочно 20 кг на 1 м³ парной для открытой каменки и 30 кг на 1 м³
для закрытой — посчитайте по своим размерам в калькуляторе выше, точный
объём каменки уточняйте по паспорту топки, если она куплена частично
готовой.

![Готовая парная с самодельной металлической печью и камнями](images/pech-dlya-bani-iz-metalla-5.jpg)

![Пар от каменки банной печи при поливе камней водой](images/pech-dlya-bani-iz-metalla-6.jpg)
