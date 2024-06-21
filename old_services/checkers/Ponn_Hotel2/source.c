#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <stdbool.h>
#include <errno.h>

#define STDOUT 1
#define STDIN 0

#define DEBUG

typedef struct user{
  char username[32];
  unsigned int balance;
  bool logged_in;
} user_t;

user_t user;

void setup(){
  memset(user.username,'\0',32);
  user.logged_in = false;
  setvbuf(stdin,0,2,0);
  setvbuf(stdout,0,2,0);
}

void parse(char * string,int max_length){
  for(int i=0; i < max_length && string[i]; i++){
    if(string[i]=='\n'){
      string[i] = '\0';
      return parse(string,max_length);
    }
  }
}

void remove_newline(char * string, int max_length){
   for(int i=0; i < max_length && string[i]; i++){
    if(string[i]=='\n'){
      string[i] = ' ';
    }
  }
}

void banner(){
  printf(" ____  _____  _  _  _  _    _   _  _____  ____  ____  __   \n\
(  _ \\(  _  )( \\( )( \\( )  ( )_( )(  _  )(_  _)( ___)(  )  \n\
 )___/ )(_)(  )  (  )  (    ) _ (  )(_)(   )(   )__)  )(__ \n\
(__)  (_____)(_)\\_)(_)\\_)  (_) (_)(_____) (__) (____)(____)\n");
}



void view_bookings(){
  char buffer[1000];
  FILE * bookings_file;

  memset(buffer,'\0',1000);

  strcpy(buffer,"./bookings/");
  strcat(buffer,user.username);
  bookings_file = fopen(buffer,"r");

  if(!bookings_file){
    printf("User has no reservations!\n");
    return;
  }

  fread(buffer,sizeof(char),0x1000,bookings_file);
  printf("Here are your reservations: \n");
  printf("%s",buffer);
  fclose(bookings_file);
}

void view_account_info(){
  char buffer[255];
  FILE * user_file;
  if(!user.logged_in){
    printf("Must be logged in.\n");
    return;
  }
  memset(buffer,'\0',255);
  strcpy(buffer,"./users/");
  strcat(buffer,user.username);
  user_file = fopen(buffer,"r");

  if(!user_file){
    printf("Error while opening user file.\n");
    return;
  }

  memset(buffer,0,255);
  
  if(fread(buffer,sizeof(char),255,user_file)==-1){
    printf("Error while reading password from stored file.\n Errno:%d",errno);
    fclose(user_file);
    return;
  }
  printf("User info:\nUsername:%s\nPassword:%s\nBalance:%d\n",user.username,buffer,user.balance);
  fclose(user_file);
}

void book_a_room(){
  char buffer[255];
  FILE * bookings_file;

  memset(buffer,'\0',255);

  strcpy(buffer,"./bookings/");
  strcat(buffer,user.username);
  bookings_file = fopen(buffer,"a");
  
  if(!bookings_file){
    printf("Error while opening file.\n");
    exit(1);
  }

  char divider[] = "=========================\nRoom:";

  strcpy(buffer,divider);
  printf("Please insert the room number you wish to book (0-255)>");
  read(STDIN,buffer+strlen(buffer),4);
  strcat(buffer,"Period:");
  printf("Insert the period you wish to book your room for (DD/MM/YYYY-DD/MM/YYYY)>");
  read(STDIN,buffer+strlen(buffer),26);
  strcat(buffer,"Notes:");
  printf("Got any notes? >");
  read(STDIN,buffer+strlen(buffer),150);
  fwrite(buffer,sizeof(char),strlen(buffer),bookings_file); 
  fclose(bookings_file);
}

void buy_souvenirs(){
  char stored_cc[0x1000];
  char credit_card[33];
  char pin[5];
  char buffer[255];
  char user_input[5];
  int choice;
  FILE * credit_card_file;
  printf("Current balance: %d\n",user.balance);
  memset(credit_card,' ',33);
  memset(stored_cc,'\0',0x1000);
  memset(user_input,'\0',5);
  memset(pin,' ',5);

  
  if(user.balance==0){
    printf("Not enough founds! Please insert your credit card detail to add some (XXXX-XXXX-XXXX-XXXX) >");
    read(STDIN,credit_card,0x20);
    remove_newline(credit_card,0x20);
    printf("Please put in the CVV (3 numbers) >");
    read(STDIN,pin,0x5);
    remove_newline(credit_card,5);
    strcpy(buffer,"./cc/");
    strcat(buffer,user.username);
    credit_card_file = fopen(buffer,"r");
    if(credit_card_file){
      printf("You got some credit card already in pipe, please wait for your previous request to be accepted.\n");
      printf("Do you wish to view your previous request?\n1) yes\n2) no\n>");
      scanf("%d",&choice);
      switch(choice){
        case 1:
          char target [] = "CVV:";
          printf("Please put in the pin to verify its you >");
          read(STDIN,pin,0x5);
          if(fread(stored_cc,sizeof(char),0x1000,credit_card_file)==-1){
            printf("Error reading credit card info. Errno: %d\n",errno);
            fclose(credit_card_file);
            return;
          }
          char * pos = strstr(stored_cc,target);
          if(!strncmp(pos+4,pin,4)){
            printf("%s\n",stored_cc);
          }
          break;
        case 2:
          return;
          break;
        default:
          printf("Invalid choice.\n");
          return;
      }
      fclose(credit_card_file);
      return;
    }
    credit_card_file = fopen(buffer,"w");
    fwrite("========================================\n",sizeof(char),41,credit_card_file);
    fwrite(credit_card,sizeof(char),0x21,credit_card_file);
    fwrite("\nCVV:",sizeof(char),0x5,credit_card_file);
    fwrite(pin,sizeof(char),0x5,credit_card_file);
    fwrite("\n========================================\n",sizeof(char),42,credit_card_file);
    fclose(credit_card_file);
    return;
  }
  else{
    printf("What do you wish to order?\n1) Ponn cup\n2) Rustell\n3) Ratafia\n4) Genziana\n5) Red wine\n >\n");
    scanf("%d",&choice);
    switch(choice){
      case 1:
        printf("Added to cart!\n");
        break;
      case 2:
        printf("Boni in culoooo!\n");
        break;
      case 3:
        printf("Slurp!\n");
        break;
      case 4:
        printf("Good look not getting drunk on this one!\n");
        break;
      case 5:
        printf("Pasteggiando!\n");
        break;
      default:
        printf("Invalid choice.\n");
        return;

    }
  }
}

void manage(){
  int choice;
  if(!user.logged_in){
    printf("Please login first!\n");
    return;
  }
  printf("Welcome %s!\n",user.username);
  while(true){
    printf("What do you want to do?\n1) Book a room\n2) Buy souvenirs\n3) View your bookings\n4) View account info\n5) Logout\n>");
    scanf("%d",&choice);
    switch(choice){
      case 1:
        book_a_room();
        break;
      case 2:
        buy_souvenirs();
        break;
      case 3:
        view_bookings();
        break;
      case 4:
        view_account_info();
        break;
      case 5:
        user.logged_in = false;
        printf("Logged out.\n");
        return;
      default:
        printf("Invalid choice.\n");
    }
  }
  return;
}



void uregister(){
  char username[32];
  char password[32];
  char buffer[255];

  memset(username,'\0',0x20);
  memset(password,'\0',0x20);
  memset(buffer,'\0',255);

  printf("Insert username >");
  read(STDIN,username,0x20);
  parse(username,0x20);
  
  strcpy(buffer,"./users/");
  strcat(buffer,username);

  FILE * user_file = fopen(buffer,"r");
  if(user_file){
    printf("User already exists!\n");
    if(fclose(user_file)){
      printf("Error closing file. Errno: %d",errno);
    }
    return;
  }

  user_file = fopen(buffer,"w");
  if(!user_file){
    printf("Error creating file.\n");
    exit(0);
  }

  printf("Insert password >");
  read(0,password,0x20);
  if(fwrite(password,sizeof(char),0x20,user_file)==-1){
    printf("Write failed. errno: %d\n",errno);
  }
  

  user.logged_in = true;
  user.balance = 0;
  strncpy(user.username,username,0x20);

  if(fclose(user_file)){
    printf("Failed to close file. Errno: %d",errno);
  }
  manage();
}

void login(){
  char username[32];
  char password[32];
  char buffer[255];

  memset(username,'\0',32);
  memset(password,'\0',32);

  printf("Insert username >");
  read(STDIN,username,0x20);
  parse(username,0x20);
  printf("Insert password >");
  read(STDIN,password,0x20);
  
  strcpy(buffer,"./users/");
  strcat(buffer,username);
  FILE * user_file =fopen(buffer,"r");

  if(!user_file){
    printf("User %s does not exist.\n",username);
    return;
  }

  char correct[32];
  int password_length;
  fread(correct,sizeof(char),0x20,user_file);
  password_length = strnlen(password,0x20);
  
  if(strncmp(password,correct,password_length)!=0){
    printf("Incorrect password.\n");
    fclose(user_file);
    return;
  }

  fclose((FILE *)user_file);

  user.logged_in = true;
  strncpy(user.username,username,0x20);
  manage();

}

void menu(){
  int choice;
  banner();
  printf("==========================================================\n");
  while(true){
    printf("1) Register\n2) Login\n3) Manage\n4) Exit\n>");
    scanf("%d",&choice);
    switch(choice){
      case 1:
        uregister();
        break;
      case 2:
        login();
        break;
      case 3:
        manage();
        break;
      case 4:
        printf("Goodbye!\n");
        return;
      default:
        printf("Invalid choice.\n");
    }
  }
}

int main(){
  setup();
  menu();
}
