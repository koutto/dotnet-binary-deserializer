using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Text;
using System.Windows.Forms;
using System.ServiceModel;
using System.ServiceModel.Channels;
using System.ServiceModel.PeerResolvers;

namespace ChatServer
{
    public partial class ChatServer : Form
    {
        private CustomPeerResolverService cprs;
        private ServiceHost host;

        public ChatServer()
        {
            InitializeComponent();            
            btnStop.Enabled = false;
        }

        private void btnStart_Click(object sender, EventArgs e)
        {
            try
            {
                cprs = new CustomPeerResolverService();
                cprs.RefreshInterval = TimeSpan.FromSeconds(5);
                host = new ServiceHost(cprs);
                cprs.ControlShape = true;
                cprs.Open();
                host.Open(TimeSpan.FromDays(1000000));
                lblMessage.Text = "Server started successfully.";
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.ToString());
            }
            finally
            {
                btnStart.Enabled = false;
                btnStop.Enabled = true;
            }
        }

        private void btnStop_Click(object sender, EventArgs e)
        {
            try
            {
                cprs.Close();
                host.Close();
                lblMessage.Text = "Server stopped successfully.";
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.ToString());
            }
            finally
            {
                btnStart.Enabled = true;
                btnStop.Enabled = false;
            }
        }
    }
}