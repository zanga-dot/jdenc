import struct, zlib

def jd15_tape(tape={"__class":"Tape","Clips":[],"TapeClock":0,"TapeBarCount":1,"FreeResourcesAfterPlay":0,"MapName":"_TestMap"},fsorder=1):
    #сделаем холадер
    #версия тэйп, основная на количестве клипов. если клипов нету, то будет 166
    tape_ver=int((166*len(tape["Clips"]))+166)
    header=struct.pack(">I",1)#"00000001"
    header+=struct.pack(">I",tape_ver)#запись версии тэйп
    header+=bytes.fromhex("9E8454600000009C")#просто часть холадера
    #запись количество клипов. если будет ошибка, то он будет 0
    try:
        header+=struct.pack(">I",len(tape["Clips"]))
    except Exception:
        header+=struct.pack(">I",0)
    #ок, холадер мы сделали
    #сделаем сами клипы
    clips=b""#пустая переменная
    #делаем список с хоалдерами для клипов
    headers=[("MotionClip",bytes.fromhex("955384A100000070")),
             ("PictogramClip",bytes.fromhex("52EC896200000038")),
             ("GoldEffectClip",bytes.fromhex("FD69B1100000001C")),
             ("KaraokeClip",bytes.fromhex("68552A4100000050"))]
    #начнем криптит наши клипы
    for clip in tape["Clips"]:
        #хоалдер самого клипа
        for __class, clipheader in headers:
            if clip["__class"] == __class:
                clips+=clipheader
        #стандартные вещей
        clips+=struct.pack(">I",clip["Id"])
        clips+=struct.pack(">I",clip["TrackId"])
        clips+=struct.pack(">I",clip["IsActive"])
        clips+=struct.pack(">I",clip["StartTime"])
        clips+=struct.pack(">I",clip["Duration"])
        if clip["__class"] == "KaraokeClip":
            clips+=struct.pack(">f",clip["Pitch"])#питч (есть только в karaokeclip)
            #слова
            clips+=struct.pack(">I",len(clip["Lyrics"]))
            clips+=clip["Lyrics"].encode()
            clips+=struct.pack(">I",clip["IsEndOfLine"])#это конец линии?
            clips+=struct.pack(">I",clip["ContentType"])#тип контента. я не знаю что это такое, если честно.
            #настройки интонации. как я понял.
            clips+=struct.pack(">I",clip["StartTimeTolerance"])
            clips+=struct.pack(">I",clip["EndTimeTolerance"])
            clips+=struct.pack(">f",clip["SemitoneTolerance"])#прикол. это число, но записываются оно в double
        elif clip["__class"] == "MotionClip":
            filename=[clip["ClassifierPath"].replace(clip["ClassifierPath"].split("/")[-1],""),clip["ClassifierPath"].split("/")[-1]]
            if fsorder==0:
                clips+=struct.pack(">I",len(filename[0]))
                clips+=filename[0].encode()
                clips+=struct.pack(">I",len(filename[1]))
                clips+=filename[1].encode()
            else:
                clips+=struct.pack(">I",len(filename[1]))
                clips+=filename[1].encode()
                clips+=struct.pack(">I",len(filename[0]))
                clips+=filename[0].encode()
            clips+=struct.pack("<I",zlib.crc32(filename[1].encode()))#хеш-сумма названия файла
            clips+=struct.pack(">I",0)#пустой бит
            clips+=struct.pack(">I",clip["GoldMove"])
            clips+=struct.pack(">I",clip["CoachId"])
            clips+=struct.pack(">I",clip["MoveType"])
            #я захотел челлендж. поэтому мы будем делать концовку вручную.
            #цвет
            clips+=struct.pack(">f",clip["Color"][3])
            clips+=struct.pack(">f",clip["Color"][2])
            clips+=struct.pack(">f",clip["Color"][1])
            clips+=struct.pack(">f",clip["Color"][0])
            #классификация
            for platform in ["X360","ORBIS","DURANGO"]:
                clips+=struct.pack(">I",3)#класс
                clips+=struct.pack(">I",int(clip["MotionPlatformSpecifics"][platform]["ScoreScale"]))
                clips+=struct.pack(">I",int(clip["MotionPlatformSpecifics"][platform]["ScoreSmoothing"]))
                try:
                    clips+=struct.pack(">f",clip["MotionPlatformSpecifics"][platform]["ScoringMode"])#semitonetolerance momentos
                except KeyError:
                    clips+=struct.pack(">I",0)
            for index in range(4): # пустые биты
                clips+=struct.pack(">I",0)#пустой бит
        elif clip["__class"] == "PictogramClip":
            filename=[clip["PictoPath"].replace(clip["PictoPath"].split("/")[-1],""),clip["PictoPath"].split("/")[-1]]
            if fsorder==0:
                clips+=struct.pack(">I",len(filename[0]))
                clips+=filename[0].encode()
                clips+=struct.pack(">I",len(filename[1]))
                clips+=filename[1].encode()
            else:
                clips+=struct.pack(">I",len(filename[1]))
                clips+=filename[1].encode()
                clips+=struct.pack(">I",len(filename[0]))
                clips+=filename[0].encode()
            clips+=struct.pack("<I",zlib.crc32(filename[1].encode()))#хеш-сумма названия файла
            clips+=struct.pack(">I",0)#пустой бит
            clips+=bytes.fromhex("FFFFFFFF")#либо altindex, либо coachcount
        elif clip["__class"] == "GoldEffectClip":
            clips+=struct.pack(">I",clip["EffectType"])
    #концовка
    ending=b""#пустая переменная
    for index in range(2): # пустые биты
        ending+=struct.pack(">I",0)#пустой бит
    ending+=struct.pack(">I",tape["TapeClock"])
    ending+=struct.pack(">I",tape["TapeBarCount"])
    ending+=struct.pack(">I",tape["FreeResourcesAfterPlay"])
    ending+=struct.pack(">I",0)#пустой бит
    ending+=struct.pack(">I",len(tape["MapName"]))
    ending+=tape["MapName"].encode()
    return header + clips + ending

def jd15_musictrack(mt={},fsorder=1,gamever=2020):
    #холадер
    if gamever<=2017:
        header=struct.pack(">I",112)
    else:
        header=struct.pack(">I",1)
    header+=struct.pack(">I",5514)#версия тпг
    header+=bytes.fromhex("1B857BCE0000006C000000000000000000000000000000000000000000000000000000000000000102883A7E000000A0000000900000006C")#нужное, я хз что это такое
    #биты
    beats=struct.pack(">I",len(mt["COMPONENTS"][0]["trackData"]["structure"]["markers"]))#количество битов
    for beat in mt["COMPONENTS"][0]["trackData"]["structure"]["markers"]:
        beats+=struct.pack(">I",beat)
    #подписи битов
    signatures=struct.pack(">I",len(mt["COMPONENTS"][0]["trackData"]["structure"]["signatures"]))#количество подписи
    for signature in mt["COMPONENTS"][0]["trackData"]["structure"]["signatures"]:
        signatures+=struct.pack(">i",8)#класс
        signatures+=struct.pack(">i",signature["marker"])#маркер (бит)
        signatures+=struct.pack(">i",signature["beats"])#количество битов в нем?
    #разделы битов
    sections=struct.pack(">I",len(mt["COMPONENTS"][0]["trackData"]["structure"]["sections"]))#количество разделов
    for section in mt["COMPONENTS"][0]["trackData"]["structure"]["sections"]:
        sections+=struct.pack(">i",20)#класс
        sections+=struct.pack(">i",section["marker"])#маркер (бит)
        sections+=struct.pack(">i",section["sectionType"])#тип раздела?
        sections+=struct.pack(">i",len(section["comment"]))#длина комментария
        sections+=section["comment"].encode()#сам комментарий
    #данные трека
    components=struct.pack(">i",mt["COMPONENTS"][0]["trackData"]["structure"]["startBeat"])#старт битов
    components+=struct.pack(">I",mt["COMPONENTS"][0]["trackData"]["structure"]["endBeat"])#конец битов
    if gamever>=2018:
        for index in range(5):
            components+=struct.pack(">h",0)
    components+=struct.pack(">f",mt["COMPONENTS"][0]["trackData"]["structure"]["videoStartTime"])#старт тейм
    if gamever==2014:
        pass
    elif gamever==2015 or gamever==2016 or gamever==2017:
        components+=struct.pack(">I",0)#пустой бит
    elif gamever>=2018:
        for index in range(5):
            components+=struct.pack(">I",0)#пустой бит
    filename=[mt["COMPONENTS"][0]["trackData"]["path"].replace(mt["COMPONENTS"][0]["trackData"]["path"].split("/")[-1],""),mt["COMPONENTS"][0]["trackData"]["path"].split("/")[-1]]
    if fsorder==0:
        components+=struct.pack(">I",len(filename[0]))
        components+=filename[0].encode()
        components+=struct.pack(">I",len(filename[1]))
        components+=filename[1].encode()
    else:
        components+=struct.pack(">I",len(filename[1]))
        components+=filename[1].encode()
        components+=struct.pack(">I",len(filename[0]))
        components+=filename[0].encode()
    components+=struct.pack("<I",zlib.crc32(filename[1].encode()))#хеш-сумма названия файла
    for index in range(2):
        components+=struct.pack(">I",0)#пустой бит
    return header + beats + signatures + sections + components
