  /*
 * Entregable_1.c
 *
 * Created: 27/04/2021 07:19:23 a. m.
 * uC    : ATMEGA328p 
 * Author : Alan Mondragón & Franco Minutti
 * This program decodes a key press in a matrix keyboard of 4x4
 * were the columns are connected to PORTD and generates and interrupt
 * to the ATMEGA328p, while the rows are connected to PORTB. The PORTC
 * is used to visualize the ascii code of the key pressed and is send 
 * to the serial port using UART protocol
 */ 

#include <avr/io.h>
#define F_CPU 16000000UL
#include <util/delay.h>
#include <avr/interrupt.h>

#define   KEY_PRTCOL  PORTD   //keyboard PORTD for columns
#define   KEY_PRTROW  PORTB   //keyboard PORTB for rows
#define   KEY_DDRD  DDRD    //keyboard DDRD
#define   KEY_DDRB  DDRB    //keyboard DDRB
#define   KEY_PIND  PIND    //keyboard PIND
#define   KEY_PINB  PINB    //keyboard PINB

unsigned char keypad[4][4] = {  '1','2','3','+', //ascii values for the 
                '4','5','6','-', //the keyboard
                '7','8','9','*',
                '.','0','=','/'};

void usart_init (void){
  
  UCSR0B = (1<<TXEN0);        //Initialize transmition of USART0
  UCSR0C = (1<<UCSZ01) | (1<<UCSZ00); //set a 8-bit character size for Tx
  //UBRR0L = 103;     //Value to set an aprox baudrate of 9600 bits/s
  Serial.begin(9600);
  
}

void usart_send(unsigned char ch){ //function to send a char using USART
  
  while(!(UCSR0A & (1<<UDRE0)));    //wait until URD0 is empty
  UDR0 = ch;              // transmit ch
}

ISR (PCINT2_vect) {         //ISR for Pin Change Interrupt 
  
  DDRC = 0xFF;        //variable physical check at  PORTC
  KEY_DDRD = 0x00;      // set PORTD bits (3 to 0) as INPUT
  KEY_DDRB = 0x0F;      // set PORTB bits (3 to 0) as OUTPUT
  KEY_PRTCOL = 0xF0;
  KEY_PRTROW = 0x0F;
  KEY_PRTCOL |= 0xF0;     //enable pull-up resistors
  unsigned char colloc, rowloc; //variables to save the key pressed
  PCMSK2 = 0x00;        // to prevent call ISR multiple times
  
  while (1) {  //keyboard routine. This sends the ASCII code of pressed key
    
    do {              //Find which column has changed
      KEY_PRTROW &= 0x00;     //ground all rows at once
      KEY_PRTCOL &= 0xF0;     
      asm("NOP");   //avoids that compiler deleted that instructions
      colloc = (KEY_PIND & 0xF0); //read the columns
    } while(colloc != 0xF0);    //check until all keys released
    
    do {
      do {
        _delay_ms(20);        //call delay for 1st debounce
        colloc = (KEY_PIND & 0xF0); //see if any key is pressed
      } while (colloc == 0xF0);   //keep checking for key press
      _delay_ms(20);          //call delay for 2nd debounce
      colloc = (KEY_PIND & 0xF0);   //read columns
    } while (colloc == 0xF0);     //wait for key press
    
    while (1){
      //Checks if row 3 has changed
      KEY_PRTROW = 0x0E;          //ground row 3
      KEY_PRTCOL = 0xF0;
      asm("NOP");   //avoids that compiler deleted that instructions
      colloc = (KEY_PIND & 0xF0);     
      if (colloc != 0xF0){        
        rowloc = 3;           //save row location
        break;              
      }
      //Checks if row 2 has changed
      KEY_PRTROW = 0x0D;          //ground row 2
      KEY_PRTCOL = 0xF0;
      asm("NOP");   //avoids that compiler deleted that instructions
      colloc = (KEY_PIND & 0xF0);     
      if (colloc != 0xF0) {       
        rowloc = 2;           //save row location
        break;              
      }
      //Checks if row 1 has changed
      KEY_PRTROW = 0x0B;          //ground row 1
      KEY_PRTCOL = 0xF0;
      asm("NOP");   //avoids that compiler deleted that instructions
      colloc = (KEY_PIND & 0xF0);     
      if (colloc != 0xF0) {
        rowloc = 1;
        break;              //exit while loop
      }
      //Checks if row 0 has changed
      KEY_PRTROW = 0x07;          //ground row 0
      KEY_PRTCOL = 0xF0;
      asm("NOP");   //avoids that compiler deleted that instructions
      colloc = (KEY_PIND & 0xF0);     //save row location
      rowloc = 0;
      break;
    }
    //Send the key presed to POTRC as ascii code
    if (colloc == 0xE0)
    PORTC = (keypad[rowloc][3]);
    else if (colloc == 0xD0)
    PORTC = (keypad[rowloc][2]);
    else if (colloc == 0xB0)
    PORTC = (keypad[rowloc][1]);
    else
    PORTC = (keypad[rowloc][0]);
    
    unsigned char i = PORTC;    //char to be send to the RPI
    usart_init();         //initialize the USART
    usart_send(i);          //Sending the key pressed
  }
  
  PCMSK2 = 0xF0;    //enable PIND interrupts again
}

int main(void) {

  PCMSK2 = 0xF0;    //enable pin change in PORTD bits (4 to 7)
  PCICR = (1<<PCIE2); //PORTD interruptions enable
  sei();          // Enable global interruptions
  
  while (1);        //wait here
  
  return 0;
}
