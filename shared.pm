package shared;
use POSIX qw/strftime/;
BEGIN {
	use Exporter ();
	@ISA = "Exporter";
	@EXPORT = qw(_log cmd);
}

# public
# Write information to LOG
sub _log{
	open (f, ">>$config::app_log");
	print f strftime('%Y-%m-%d %H:%M:%S',localtime)." : ${_[0]}\n";
	close (f);
}

# private
# Send SOA packet
sub send_soa{
    open my $fh, $_[0]." |" or die "Cannot run command: $!";
    {
      local $/;
      my $var = <$fh>;
      return $var;
    }
    close $fh;
}

# private
# Get next bras address
sub next_bras{	
		
	if ($_[0] eq "172.16.0.11") {
		return "172.16.0.12";
	} else {
		return "172.16.0.11";
	}
}

# public
sub cmd{

  my $command = $_[0];
  my $bras_key = $_[1];
  my $bras_val;
  if ($bras_key eq "") {
	$bras_key = next_bras($bras_key);
	$bras_val = $config::brases{$bras_key};	
  } else {
	$bras_val = $config::brases{$bras_key};	
  }
  
#  return false;
  my $user = $_[2];
  my $session = $_[3];
  my $service = $_[4];
  for($i = 0; $i < scalar(keys %config::brases); $i++) {    
	my $cmd = "$config::app_echo \"User-Name=\\\"$user\\\",Acct-Session-Id=\\\"$session\\\",cisco-avpair=\\\"subscriber:command=$command\\\",cisco-avpair=\\\"subscriber:service-name=$service\\\"\" | $config::app_client -x $bras_val";  
	my $result = send_soa($cmd);	
	_log($result);
	if (index($result, "CoA-ACK") != -1 ) { last;}	
	_log("BRAS NOT FOUND TRY NEXT...\n");
	$bras_key = next_bras($bras_key);
	$bras_val = $config::brases{$bras_key};
  }  
}

return 1;
END { }
