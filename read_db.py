#reprez corecta e zi.luna.an
#preiau luna/zi/an
a = '04/23/95'

def correct_date(date):
	zi = date.split('/')[1]
	luna = date.split('/')[0]
	if int(date.split('/')[2]) in range(0,89):
		an = '20' + date.split('/')[2]
	else:
		an = '19'+date.split('/')[2]
 	return (zi+'.'+luna+'.'+an)

a = correct_date('06/09/04')
print a
		
		




		
		
	







		


