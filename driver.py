import sys
import D112 as D112
from dbfpy import dbf

#read ANGAJ.DBF and fill in data
angajator = dbf.Dbf("input/ANGAJATOR.DBF")

#read ANGAJ.DBF and fill in data
angajat = dbf.Dbf("input/ANGAJAT.DBF")

#instantiate classes
#informatii din sectiunea <declaratieUnica>
declaratieUnica = D112.declaratieUnica()

#informatii din sectiunea <angajator>
declaratieUnica.angajator = D112.AngajatorType()


#nr. inregistrari din <angajatorA>
#determinam numarul dupa numar de inregistrari de tipul A_codOblig
angA = []
for values in angajator:
	angA.append(values["A_codOblig"])
size_angA = len(angA)


#nr. inregistrari angajati inclusiv inregistrarile cu IDASIG == 0 
ids = []
for value in angajat:
	ids.append(value["IDASIG"])
size_total_angajati = len(ids)


#informatii din sectiunea <declaratieUnica>
declaratieUnica.luna_r = angajator[0]['LUNA_R']
declaratieUnica.an_r = angajator[0]['AN_R']
declaratieUnica.d_rec = angajator[0]['D_REC']
declaratieUnica.nume_declar = angajator[0]['NUME_D']
declaratieUnica.prenume_declar = angajator[0]['PRENUME_D']
declaratieUnica.functie_declar = angajator[0]['FUNCTIE_D']

#informatii din sectiunea <angajator>
declaratieUnica.angajator.cif = angajator[0]['CIF']
declaratieUnica.angajator.rgCom = angajator[0]['RGCOM']
declaratieUnica.angajator.caen = angajator[0]['CAEN']
declaratieUnica.angajator.den = angajator[0]['DEN']
declaratieUnica.angajator.adrSoc = angajator[0]['ADRSOC']
declaratieUnica.angajator.telSoc = angajator[0]['TELSOC']
declaratieUnica.angajator.faxSoc = angajator[0]['FAXSOC']
declaratieUnica.angajator.mailSoc = angajator[0]['MAILSOC']
if (angajator[0]['ADRFISC']):
	declaratieUnica.angajator.adrFisc = angajator[0]['ADRFISC']
if (angajator[0]['TELFISC']):
	declaratieUnica.angajator.telFisc = angajator[0]['TELFISC']
if (angajator[0]['FAXFISC']):
	declaratieUnica.angajator.faxFisc = angajator[0]['FAXFISC']
if (angajator[0]['MAILFISC']):
	declaratieUnica.angajator.mailFisc = angajator[0]['MAILFISC']
declaratieUnica.angajator.casaAng = angajator[0]['CASAANG']
declaratieUnica.angajator.tRisc = angajator[0]['TRISC']
declaratieUnica.angajator.dat = angajator[0]['DAT']
declaratieUnica.angajator.totalPlata_A=angajator[0]['TOTPLATA']

#informatii <angajatorA>
for index in range(size_angA):
	#creaza un <angajatorA> pentru fiecare obligatie
	angajatorA = D112.AngajatorAType()	
	angajatorA.A_codOblig = angajator[index]['A_CODOBLIG']
	angajatorA.A_codBugetar = angajator[index]['A_CODBUGET']
	angajatorA.A_datorat = angajator[index]['A_DATORAT']
	if (angajator[index]['A_DEDUCTIB']):
		angajatorA.A_deductibil = angajator[index]['A_DEDUCTIB']
	angajatorA.A_plata = angajator[index]['A_PLATA']
	#adauga <angajatorA> in XML
	declaratieUnica.angajator.add_angajatorA(angajatorA)

#informatii <angajatorB>
angajatorB = D112.AngajatorBType()
angajatorB.B_cnp = angajator[0]['B_CNP']
angajatorB.B_sanatate = angajator[0]['B_SANATATE']
angajatorB.B_pensie = angajator[0]['B_PENSIE']
angajatorB.B_brutSalarii = angajator[0]['B_BRUTSAL']
#adauga <angajatorB> in XML
declaratieUnica.angajator.set_angajatorB(angajatorB)

#informatii <angajatorC1>
angajatorC1 = D112.AngajatorC1Type()
if (angajator[0]['C1_11']):
	angajatorC1.C1_11 = angajator[0]['C1_11']
if (angajator[0]['C1_12']):
	angajatorC1.C1_12 = angajator[0]['C1_12']
if(angajator[0]['C1_13']):
	angajatorC1.C1_13 = angajator[0]['C1_13']
if(angajator[0]['C1_21']):
	angajatorC1.C1_21 = angajator[0]['C1_21']
if(angajator[0]['C1_22']):
	angajatorC1.C1_22 = angajator[0]['C1_22']
if(angajator[0]['C1_23']):
	angajatorC1.C1_23 = angajator[0]['C1_23']
if(angajator[0]['C1_31']):
	angajatorC1.C1_31 = angajator[0]['C1_31']
if(angajator[0]['C1_32']):
	angajatorC1.C1_32 = angajator[0]['C1_32']
if(angajator[0]['C1_33']):
	angajatorC1.C1_33 = angajator[0]['C1_33']
if(angajator[0]['C1_T1']):
	angajatorC1.C1_T1 = angajator[0]['C1_T1']
if(angajator[0]['C1_T2']):
	angajatorC1.C1_T2 = angajator[0]['C1_T2']
if(angajator[0]['C1_T']):
	angajatorC1.C1_T = angajator[0]['C1_T']
if(angajator[0]['C1_T3']):
	angajatorC1.C1_T3 = angajator[0]['C1_T3']
if(angajator[0]['C1_5']):
	angajatorC1.C1_5 = angajator[0]['C1_5']
if(angajator[0]['C1_6']):
	angajatorC1.C1_6 = angajator[0]['C1_6']
if(angajator[0]['C1_7']):
	angajatorC1.C1_7 = angajator[0]['C1_7']
#adauga <angajatorC1> in XML
declaratieUnica.angajator.set_angajatorC1(angajatorC1)


#informatii <angajatorC2>
angajatorC2 = D112.AngajatorC2Type()
if(angajator[0]['C2_11']):
	angajatorC2.C2_11 = angajator[0]['C2_11']
if(angajator[0]['C2_12']):
	angajatorC2.C2_12 = angajator[0]['C2_12']
if(angajator[0]['C2_13']):
	angajatorC2.C2_13 = angajator[0]['C2_13']
if(angajator[0]['C2_14']):
	angajatorC2.C2_14 = angajator[0]['C2_14']
if(angajator[0]['C2_15']):
	angajatorC2.C2_15 = angajator[0]['C2_15']
if(angajator[0]['C2_16']):
	angajatorC2.C2_16 = angajator[0]['C2_16']
if(angajator[0]['C2_21']):
	angajatorC2.C2_21 = angajator[0]['C2_21']
if(angajator[0]['C2_22']):
	angajatorC2.C2_22 = angajator[0]['C2_22']
if(angajator[0]['C2_24']):
	angajatorC2.C2_24 = angajator[0]['C2_24']
if(angajator[0]['C2_26']):
	angajatorC2.C2_26 = angajator[0]['C2_26']
if(angajator[0]['C2_31']):
	angajatorC2.C2_31 = angajator[0]['C2_31']
if(angajator[0]['C2_32']):
	angajatorC2.C2_32 = angajator[0]['C2_32']
if(angajator[0]['C2_34']):
	angajatorC2.C2_34 = angajator[0]['C2_34']
if(angajator[0]['C2_36']):
	angajatorC2.C2_36 = angajator[0]['C2_36']
if(angajator[0]['C2_41']):
	angajatorC2.C2_41 = angajator[0]['C2_41']
if(angajator[0]['C2_42']):
	angajatorC2.C2_42 = angajator[0]['C2_42']
if(angajator[0]['C2_44']):
	angajatorC2.C2_44 = angajator[0]['C2_44']
if(angajator[0]['C2_46']):
	angajatorC2.C2_46 = angajator[0]['C2_46']
if(angajator[0]['C2_51']):
	angajatorC2.C2_51 = angajator[0]['C2_51']
if(angajator[0]['C2_52']):
	angajatorC2.C2_52 = angajator[0]['C2_52']
if(angajator[0]['C2_56']):
	angajatorC2.C2_54 = angajator[0]['C2_56']
if(angajator[0]['C2_T6']):
	angajatorC2.C2_T6 = angajator[0]['C2_T6']
if(angajator[0]['C2_7']):
	angajatorC2.C2_7 = angajator[0]['C2_7']
if(angajator[0]['C2_8']):
	angajatorC2.C2_8 = angajator[0]['C2_8']
if(angajator[0]['C2_9']):
	angajatorC2.C2_9 = angajator[0]['C2_9']
if(angajator[0]['C2_10']):
	angajatorC2.C2_10 = angajator[0]['C2_10']
if(angajator[0]['C2_110']):
	angajatorC2.C2_110 = angajator[0]['C2_110']
if(angajator[0]['C2_120']):
	angajatorC2.C2_120 = angajator[0]['C2_120']
if(angajator[0]['C2_130']):
	angajatorC2.C2_130 = angajator[0]['C2_130']
#adauga <angajatorC2> in XML
declaratieUnica.angajator.set_angajatorC2(angajatorC2)


#informatii <angajatorC3>
angajatorC3 = D112.AngajatorC3Type()
if (angajator[0]['C3_11']):
	angajatorC3.C3_11 = angajator[0]['C3_11']
if(angajator[0]['C3_12']):
	angajatorC3.C3_12 = angajator[0]['C3_12']
if(angajator[0]['C3_13']):
	angajatorC3.C3_13 = angajator[0]['C3_13']
if(angajator[0]['C3_14']):
	angajatorC3.C3_14 = angajator[0]['C3_14']
if(angajator[0]['C3_21']):
	angajatorC3.C3_21 = angajator[0]['C3_21']
if(angajator[0]['C3_22']):
	angajatorC3.C3_22 = angajator[0]['C3_22']
if(angajator[0]['C3_23']):
	angajatorC3.C3_23 = angajator[0]['C3_23']
if(angajator[0]['C3_24']):
	angajatorC3.C3_24 = angajator[0]['C3_24']
if(angajator[0]['C3_31']):
	angajatorC3.C3_31 = angajator[0]['C3_31']
if(angajator[0]['C3_32']):
	angajatorC3.C3_32 = angajator[0]['C3_32']
if(angajator[0]['C3_33']):
	angajatorC3.C3_33 = angajator[0]['C3_33']
if(angajator[0]['C3_34']):
	angajatorC3.C3_34 = angajator[0]['C3_34']
if(angajator[0]['C3_41']):
	angajatorC3.C3_41 = angajator[0]['C3_41']
if(angajator[0]['C3_42']):
	angajatorC3.C3_42 = angajator[0]['C3_42']
if(angajator[0]['C3_43']):
	angajatorC3.C3_43 = angajator[0]['C3_43']
if(angajator[0]['C3_44']):
	angajatorC3.C3_44 = angajator[0]['C3_44']
if(angajator[0]['C3_TOTAL']):
	angajatorC3.C3_total = angajator[0]['C3_TOTAL']
if(angajator[0]['C3_SUMA']):
	angajatorC3.C3_suma = angajator[0]['C3_SUMA']
if(angajator[0]['C3_AJ_NR']):
	angajatorC3.C3_aj_nr = angajator[0]['C3_AJ_NR']
if(angajator[0]['C3_AJ_SUMA']):
	angajatorC3.C3_aj_suma = angajator[0]['C3_AJ_SUMA']
#adauga <angajatorC3> in XML
declaratieUnica.angajator.set_angajatorC3(angajatorC3)

#informatii <angajatorC4>
angajatorC4 = D112.AngajatorC4Type()
if(angajator[0]['C4_SCUTITS']):
	angajatorC4.C4_scutitaSo = angajator[0]['C4_SCUTITS']
#adauga <angajatorC4> in XML
declaratieUnica.angajator.set_angajatorC4(angajatorC4)

#informatii <angajatorC5>
angajatorC5 = D112.AngajatorC5Type()
if(angajator[0]['C5_SUBV']):
	angajatorC5.C5_subv = angajator[0]['C5_SUBV']
if(angajator[0]['C5_RECUPER']):
	angajatorC5.C5_recuperat = angajator[0]['C5_RECUPER']
if(angajator[0]['C5_RESTITU']):
	angajatorC5.C5_restituit = angajator[0]['C5_RESTITU']
#adauga <angajatorC5> in XML
declaratieUnica.angajator.add_angajatorC5(angajatorC5)

#informatii <angajatorC6>
angajatorC6 = D112.AngajatorC6Type()
angajatorC6.C6_baza = angajator[0]['C6_BAZA']
angajatorC6.C6_ct = angajator[0]['C6_CT']
#adauga <angajatorC6> in XML
declaratieUnica.angajator.set_angajatorC6(angajatorC6)

#informatii <angajatorC7>
angajatorC7 = D112.AngajatorC7Type()
if(angajator[0]['C7_BAZA']):
	angajatorC7.C7_baza = angajator[0]['C7_BAZA']
if(angajator[0]['C7_CT']):
	angajatorC7.C7_ct = angajator[0]['C7_CT']
#adauga <angajatorC7> in XML
declaratieUnica.angajator.set_angajatorC7(angajatorC7)

#informatii <angajatorD>
angajatorD = D112.AngajatorDType()
angajatorD.D1 = angajator[0]['D1']
#adauga <angajatorD> in XML
declaratieUnica.angajator.set_angajatorD(angajatorD)

#informatii <angajatorF1>
angajatorF1 = D112.AngajatorF1Type()
if(angajator[0]['F1_SUMA']):
	angajatorF1.F1_suma = angajator[0]['F1_SUMA']
#adauga <angajatorF1> in XML
declaratieUnica.angajator.set_angajatorF1(angajatorF1)


for index in range(size_total_angajati):
	if (angajat[index]['IDASIG']):
		asigurat = D112.AsiguratType()
		asigurat.cnpAsig = angajat[index]['CNPASIG']
		asigurat.idAsig = angajat[index]['IDASIG']
		if (angajat[index]['NUMEASIG']):
			asigurat.numeAsig = angajat[index]['NUMEASIG']
		if (angajat[index]['PRENASIG']):
			asigurat.prenAsig = angajat[index]['PRENASIG']
		if (angajat[index]['CNPANT']):
			asigurat.cnpAnt = angajat[index]['CNPANT']
		if (angajat[index]['NUMEANT']):
			asigurat.numeAnt = angajat[index]['NUMEANT']
		if (angajat[index]['PRENANT']):
			asigurat.prenAnt = angajat[index]['PRENANT']
		if (angajat[index]['DATAANG']):
			#asigurat.dataAng = angajat[index]['DATAANG']
			data = angajat[index]['DATAANG']
			asigurat.dataAng= str(data.day)+'.'+str(data.month)+'.'+str(data.year)
		if (angajat[index]['DATASF']):
			data = angajat[index]['DATASF']
			asigurat.dataSf = str(data.day)+'.'+str(data.month)+'.'+str(data.year)
		if (angajat[index]['CASASN']):
			asigurat.casaSn = angajat[index]['CASASN']
		if (angajat[index]['ASIGCI']):
			asigurat.asigCI = angajat[index]['ASIGCI']
		if (angajat[index]['ASIGSO']):
			asigurat.asigSO = angajat[index]['ASIGSO']
		
		#informatii <coAsigurati>
		#verific daca exista valori valide pentru NUME, PRENUME si TIP
		#Generez tag-uri numai pentru NUME, PRENUME si TIP != None
		if ((angajat[index]['NUME'] != '') & (angajat[index]['PRENUME'] != '') & (angajat[index]['TIP'] != '')):
			coAsigurati = D112.CoAsiguratiType()
			coAsigurati.tip=angajat[index]['TIP']
			coAsigurati.cnp=angajat[index]['CNP']
			coAsigurati.nume=angajat[index]['NUME']
			coAsigurati.prenume=angajat[index]['PRENUME']
			#adauga <coAsigurati> in XML
			asigurat.add_coAsigurati(coAsigurati)
			
		#informatii <asiguratA>
		#verific daca am campuri pentru acest gen de asigurat (verific prin campul obligatoriu A_3)
		#daca nu exista nu adaug tagul <asiguratA> - vezi cazul ILLES SABIN
		if (angajat[index]['A_3']):
			asiguratA = D112.AsiguratAType()
			asiguratA.A_1 = angajat[index]['A_1']
			asiguratA.A_2 = angajat[index]['A_2']
			asiguratA.A_3 = angajat[index]['A_3']
			asiguratA.A_4 = angajat[index]['A_4']
			if (angajat[index]['A_5']):
				asiguratA.A_5 = angajat[index]['A_5']
			if (angajat[index]['A_6']):
				asiguratA.A_6 = angajat[index]['A_6']
			if (angajat[index]['A_7']):
				asiguratA.A_7 = angajat[index]['A_7']
			if (angajat[index]['A_8']):
				asiguratA.A_8 = angajat[index]['A_8']
			if (angajat[index]['A_9']):
				asiguratA.A_9 = angajat[index]['A_9']
			if (angajat[index]['A_10']):
				asiguratA.A_10 = angajat[index]['A_10']
			asiguratA.A_11 = angajat[index]['A_11']
			asiguratA.A_12 = angajat[index]['A_12']
			asiguratA.A_13 = angajat[index]['A_13']
			asiguratA.A_14 = angajat[index]['A_14']
			asiguratA.A_20 = angajat[index]['A_20']
			#adauga <asiguratA> in XML
			asigurat.set_asiguratA(asiguratA)
		#informatii <asiguratB1>
		#verific daca am campuri pentru acest gen de asigurat (verific prin campul B1_3)
		if (angajat[index]['B1_3']):
			asiguratB1 = D112.AsiguratB1Type()
			asiguratB1.B1_1 = angajat[index]['B1_1']
			asiguratB1.B1_2 = angajat[index]['B1_2']
			asiguratB1.B1_3 = angajat[index]['B1_3']
			asiguratB1.B1_4 = angajat[index]['B1_4']
			asiguratB1.B1_5 = angajat[index]['B1_5']
			asiguratB1.B1_6 = angajat[index]['B1_6']
			asiguratB1.B1_7 = angajat[index]['B1_7']
			asiguratB1.B1_8 = angajat[index]['B1_8']
			asiguratB1.B1_9 = angajat[index]['B1_9']
			asiguratB1.B1_10 = angajat[index]['B1_10']
			asiguratB1.B1_15 = angajat[index]['B1_15']
			#adauga <asiguratB1> in XML
			asigurat.add_asiguratB1(asiguratB1)
		#informatii <asiguratB2>
		#verific daca campurile exista - vezi cazul MAN LAVINIA
		if (angajat[index]['B2_1'] | angajat[index]['B2_2'] | angajat[index]['B2_3'] | angajat[index]['B2_4'] |  angajat[index]['B2_5'] | angajat[index]['B2_6'] | angajat[index]['B2_7']):
			asiguratB2 = D112.AsiguratB2Type()
			if (angajat[index]['B2_1']):
				asiguratB2.B2_1 = angajat[index]['B2_1']
			if (angajat[index]['B2_2']):
				asiguratB2.B2_2 = angajat[index]['B2_2']
			if(angajat[index]['B2_3']):
				asiguratB2.B2_3 = angajat[index]['B2_3']
			if(angajat[index]['B2_4']):
				asiguratB2.B2_4 = angajat[index]['B2_4']
			if (angajat[index]['B2_5']):
				asiguratB2.B2_5 = angajat[index]['B2_5']
			if(angajat[index]['B2_6']):
				asiguratB2.B2_6 = angajat[index]['B2_6']
			if(angajat[index]['B2_7']):
				asiguratB2.B2_7 = angajat[index]['B2_7']
			#adauga <asiguratB1> in XML
			asigurat.set_asiguratB2(asiguratB2)
			
		if (angajat[index]['B3_1'] | angajat[index]['B3_2'] | angajat[index]['B3_3'] | angajat[index]['B3_4'] | angajat[index]['B3_5'] | angajat[index]['B3_6'] | angajat[index]['B3_7'] | angajat[index]['B3_8'] | angajat[index]['B3_9'] | angajat[index]['B3_10'] | angajat[index]['B3_11'] | angajat[index]['B3_12'] | angajat[index]['B3_13']):
			asiguratB3 = D112.AsiguratB3Type()
			if (angajat[index]['B3_1']):
				asiguratB3.B3_1 = angajat[index]['B3_1'] 
			if (angajat[index]['B3_2']):
				asiguratB3.B3_2 = angajat[index]['B3_2']
			if (angajat[index]['B3_3']):
				asiguratB3.B3_3 = angajat[index]['B3_3']
			if (angajat[index]['B3_4']):
				asiguratB3.B3_4 = angajat[index]['B3_4']
			if (angajat[index]['B3_5']):
				asiguratB3.B3_5 = angajat[index]['B3_5']
			if (angajat[index]['B3_6']):
				asiguratB3.B3_6 = angajat[index]['B3_6']
			if (angajat[index]['B3_7']):
				asiguratB3.B3_7 = angajat[index]['B3_7']
			if (angajat[index]['B3_8']):
				asiguratB3.B3_8 = angajat[index]['B3_8']
			if (angajat[index]['B3_9']):
				asiguratB3.B3_9 = angajat[index]['B3_9']
			if (angajat[index]['B3_10']):
				asiguratB3.B3_10 = angajat[index]['B3_10']
			if (angajat[index]['B3_11']):
				asiguratB3.B3_11 = angajat[index]['B3_11']
			if (angajat[index]['B3_12']):
				asiguratB3.B3_12 = angajat[index]['B3_12']
			if (angajat[index]['B3_13']):
				asiguratB3.B3_13 = angajat[index]['B3_13']
			#adauga <asiguratB3> in XML
			asigurat.set_asiguratB3(asiguratB3)
			
		#informatii <asiguratB4>
		if (angajat[index]['B4_1'] | angajat[index]['B4_2'] | angajat[index]['B4_3'] | angajat[index]['B4_4'] | angajat[index]['B4_5'] | angajat[index]['B4_6'] | angajat[index]['B4_7'] | angajat[index]['B4_8'] | angajat[index]['B4_14']):
			asiguratB4 = D112.AsiguratB4Type()
			if (angajat[index]['B4_1']):
				asiguratB4.B4_1 = angajat[index]['B4_1']
			if (angajat[index]['B4_2']):
				asiguratB4.B4_2 = angajat[index]['B4_2']
			if (angajat[index]['B4_3']):
				asiguratB4.B4_3 = angajat[index]['B4_3']
			if (angajat[index]['B4_4']):
				asiguratB4.B4_4 = angajat[index]['B4_4']
			if (angajat[index]['B4_5']):
				asiguratB4.B4_5 = angajat[index]['B4_5']
			if (angajat[index]['B4_6']):
				asiguratB4.B4_6 = angajat[index]['B4_6']
			if (angajat[index]['B4_7']):
				asiguratB4.B4_7 = angajat[index]['B4_7']
			if (angajat[index]['B4_8']):
				asiguratB4.B4_8 = angajat[index]['B4_8']
			if (angajat[index]['B4_14']):
				asiguratB4.B4_14 = angajat[index]['B4_14']
			#adauga <asiguratB4> in XML
			asigurat.set_asiguratB4(asiguratB4)
			
		#informatii <asiguratD>
		#verific daca exista D_1 - serie de concediu, daca nu exista nu adaug <asiguratD>
		if (angajat[index]['D_1']):
			asiguratD = D112.AsiguratDType()
			asiguratD.D_1 = angajat[index]['D_1']
			asiguratD.D_2 = angajat[index]['D_2']
			if (angajat[index]['D_3']):
				asiguratD.D_3 = angajat[index]['D_3']
			if (angajat[index]['D_4']):
				asiguratD.D_4 = angajat[index]['D_4']
			data_D_5 = angajat[index]['D_5']	
			asiguratD.D_5 = str(data_D_5.day)+'.'+str(data_D_5.month)+'.'+str(data_D_5.year)
			data_D_6 = angajat[index]['D_6']
			asiguratD.D_6 = str(data_D_6.day)+'.'+str(data_D_6.month)+'.'+str(data_D_6.year)
			data_D_7 = angajat[index]['D_7']
			asiguratD.D_7 = str(data_D_7.day)+'.'+str(data_D_7.month)+'.'+str(data_D_7.year)
			if (angajat[index]['D_8']):
				asiguratD.D_8 = angajat[index]['D_8']
			asiguratD.D_9 = angajat[index]['D_9']
			asiguratD.D_10 = angajat[index]['D_10']
			if (angajat[index]['D_11']):
				asiguratD.D_11 = angajat[index]['D_11']
			if (angajat[index]['D_12']):
				asiguratD.D_12 = angajat[index]['D_12']
			if (angajat[index]['D_13']):
				asiguratD.D_13 = angajat[index]['D_13']
			if (angajat[index]['D_14']):
				asiguratD.D_14 = angajat[index]['D_14']
			else:
				asiguratD.D_14 = 0
			if (angajat[index]['D_15']):
				asiguratD.D_15 = angajat[index]['D_15']
			else:
				asiguratD.D_15 = 0
			if (angajat[index]['D_16']):
				asiguratD.D_16 = angajat[index]['D_16']
			else:
				asiguratD.D_16 = 0
			if (angajat[index]['D_17']):
				asiguratD.D_17 = angajat[index]['D_17']
			else:
				asiguratD.D_17 = 0
			if (angajat[index]['D_18']):
				asiguratD.D_18 = angajat[index]['D_18']
			else:
				asiguratD.D_18 = 0
			if (angajat[index]['D_19']):
				asiguratD.D_19 = angajat[index]['D_19']
			else:
				asiguratD.D_19 = 0
			if (angajat[index]['D_20']):
				asiguratD.D_20 = angajat[index]['D_20']
			else:
				asiguratD.D_20 = 0
			if (angajat[index]['D_21']):
				asiguratD.D_21 = angajat[index]['D_21']
			else:
				asiguratD.D_21 = 0
			#adauga <asiguratD> in XML
			asigurat.add_asiguratD(asiguratD)
			
		#adauga <asigurat>
		declaratieUnica.add_asigurat(asigurat)
		
	else:
		if (angajat[index]['D_1']):
			asiguratD = D112.AsiguratDType()
			asiguratD.D_1 = angajat[index]['D_1']
			asiguratD.D_2 = angajat[index]['D_2']
			if (angajat[index]['D_3']):
				asiguratD.D_3 = angajat[index]['D_3']
			if (angajat[index]['D_4']):
				asiguratD.D_4 = angajat[index]['D_4']
			data_D_5 = angajat[index]['D_5']	
			asiguratD.D_5 = str(data_D_5.day)+'.'+str(data_D_5.month)+'.'+str(data_D_5.year)
			data_D_6 = angajat[index]['D_6']
			asiguratD.D_6 = str(data_D_6.day)+'.'+str(data_D_6.month)+'.'+str(data_D_6.year)
			data_D_7 = angajat[index]['D_7']
			asiguratD.D_7 = str(data_D_7.day)+'.'+str(data_D_7.month)+'.'+str(data_D_7.year)
			if (angajat[index]['D_8']):
				asiguratD.D_8 = angajat[index]['D_8']
			asiguratD.D_9 = angajat[index]['D_9']
			asiguratD.D_10 = angajat[index]['D_10']
			if (angajat[index]['D_11']):
				asiguratD.D_11 = angajat[index]['D_11']
			if (angajat[index]['D_12']):
				asiguratD.D_12 = angajat[index]['D_12']
			if (angajat[index]['D_13']):
				asiguratD.D_13 = angajat[index]['D_13']
			if (angajat[index]['D_14']):
				asiguratD.D_14 = angajat[index]['D_14']
			else:
				asiguratD.D_14 = 0
			if (angajat[index]['D_15']):
				asiguratD.D_15 = angajat[index]['D_15']
			else:
				asiguratD.D_15 = 0
			if (angajat[index]['D_16']):
				asiguratD.D_16 = angajat[index]['D_16']
			else:
				asiguratD.D_16 = 0
			if (angajat[index]['D_17']):
				asiguratD.D_17 = angajat[index]['D_17']
			else:
				asiguratD.D_17 = 0
			if (angajat[index]['D_18']):
				asiguratD.D_18 = angajat[index]['D_18']
			else:
				asiguratD.D_18 = 0
			if (angajat[index]['D_19']):
				asiguratD.D_19 = angajat[index]['D_19']
			else:
				asiguratD.D_19 = 0
			if (angajat[index]['D_20']):
				asiguratD.D_20 = angajat[index]['D_20']
			else:
				asiguratD.D_20 = 0
			if (angajat[index]['D_21']):
				asiguratD.D_21 = angajat[index]['D_21']
			else:
				asiguratD.D_21 = 0
			#adauga <asiguratD> in XML
			#adaug <asiguratD> pentru ultimul asigurat adaugat in XML
			declaratieUnica.asigurat[-1].add_asiguratD(asiguratD)		
						
		
		
declaratieUnica.export(sys.stdout, 0, namespacedef_='xmlns=\'mfp:anaf:dgti:declaratie_unica:declaratie:v1\'')








